"""Create a minimal PROM bounded-context module without business logic."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def main(name: str) -> int:
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,48}", name):
        raise ValueError("Module name must use lowercase letters, digits, and hyphens")
    package = name.replace("-", "_")
    component = package.title().replace("_", "")
    module_root = ROOT / "apps" / name
    if module_root.exists():
        raise FileExistsError(f"Module already exists: {module_root}")

    write(
        module_root / "README.md",
        (
            f"# {name}\n\n"
            "Bounded PROM product module scaffold. Add domain behavior deliberately.\n"
        ),
    )
    write(
        module_root / "backend" / "src" / package / "__init__.py",
        f'"""{name} product module."""\n',
    )
    write(
        module_root / "backend" / "src" / package / "bootstrap" / "app.py",
        f'''from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="PROM {name}", version="1.0.0")

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {{"status": "live"}}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {{"status": "ready"}}

    return app


app = create_app()
''',
    )
    write(
        module_root / "backend" / "pyproject.toml",
        f'''[build-system]
requires = ["setuptools>=70.0"]
build-backend = "setuptools.build_meta"

[project]
name = "prom-{name}"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
  "fastapi>=0.136.3,<0.137.0",
  "prom-platform-sdk>=0.1.0",
  "uvicorn[standard]>=0.35.0,<1.0.0",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.28.0,<1.0.0",
  "pytest>=8.4.0,<9.0.0",
  "ruff>=0.14.0,<1.0.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.uv.sources]
prom-platform-sdk = {{ workspace = true }}
''',
    )
    write(
        module_root / "backend" / "Dockerfile",
        f'''FROM ghcr.io/astral-sh/uv:0.11.29 AS uv
FROM python:3.14.6-slim@sha256:d3400aa122fa42cf0af0dbe8ec3091b047eac5c8f7e3539f7135e86d855dc015
COPY --from=uv /uv /uvx /bin/
WORKDIR /workspace
ENV UV_LINK_MODE=copy \\
    UV_COMPILE_BYTECODE=1 \\
    PATH="/workspace/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
COPY packages/python/platform-sdk packages/python/platform-sdk
COPY apps/{name}/backend apps/{name}/backend
RUN uv sync --frozen --no-dev --package prom-{name}
WORKDIR /workspace/apps/{name}/backend
USER 65532
CMD ["python", "-m", "uvicorn", "{package}.bootstrap.app:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    )
    write(
        module_root / "backend" / "tests" / "test_health.py",
        f'''from fastapi.testclient import TestClient

from {package}.bootstrap.app import create_app


def test_health_contract() -> None:
    client = TestClient(create_app())
    assert client.get("/health/live").json() == {{"status": "live"}}
    assert client.get("/health/ready").json() == {{"status": "ready"}}
''',
    )
    write(
        module_root / "frontend" / "package.json",
        f'''{{
  "name": "@prom/{name}-frontend",
  "private": true,
  "type": "module",
  "dependencies": {{
    "@prom/platform-contracts": "0.1.0"
  }},
  "peerDependencies": {{
    "react": "19.2.7",
    "react-router-dom": "7.18.1"
  }}
}}
''',
    )
    write(
        module_root / "frontend" / "manifest.ts",
        f'''import type {{ PlatformModuleManifest }} from "@prom/platform-contracts";

export const {package}Manifest: PlatformModuleManifest = {{
  id: "{name}",
  title: "{name}",
  basePath: "/{name}",
  routePrefixes: ["/{name}"],
  requiredPermissions: ["{package}.access"],
  loadRoutes: () => import("./routes"),
  navigation: [{{ id: "{name}", title: "{name}", path: "/{name}" }}],
}};
''',
    )
    write(
        module_root / "frontend" / "routes.tsx",
        f'''export default function {component}Routes() {{
  return <main>PROM module {name} is ready for implementation.</main>;
}}
''',
    )
    write(
        module_root / "frontend" / "api" / "queryKeys.ts",
        f'''export const {package}QueryKeys = {{
  root: ["{name}"] as const,
}};
''',
    )
    print(f"Created module scaffold: apps/{name}")
    print("Next: register the manifest, run uv lock, npm install, and architecture-check.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: create_module.py <module-name>")
    raise SystemExit(main(sys.argv[1]))
