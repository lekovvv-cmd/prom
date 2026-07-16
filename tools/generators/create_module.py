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
    module_root = ROOT / "apps" / name
    if module_root.exists():
        raise FileExistsError(f"Module already exists: {module_root}")

    write(module_root / "README.md", f"# {name}\n\nBounded PROM product module scaffold. Add domain behavior deliberately.\n")
    write(module_root / "backend" / "src" / package / "__init__.py", f'"""{name} product module."""\n')
    write(module_root / "backend" / "src" / package / "bootstrap" / "app.py", f'''from fastapi import FastAPI\n\n\ndef create_app() -> FastAPI:\n    app = FastAPI(title="PROM {name}", version="1.0.0")\n\n    @app.get("/health/live")\n    def live() -> dict[str, str]:\n        return {{"status": "live"}}\n\n    @app.get("/health/ready")\n    def ready() -> dict[str, str]:\n        return {{"status": "ready"}}\n\n    return app\n\n\napp = create_app()\n''')
    write(module_root / "backend" / "pyproject.toml", f'''[build-system]\nrequires = ["setuptools>=70.0"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "prom-{name}"\nversion = "0.1.0"\nrequires-python = ">=3.14"\ndependencies = ["fastapi>=0.136.3,<0.137.0", "prom-platform-sdk>=0.1.0", "uvicorn[standard]>=0.35.0,<1.0.0"]\n\n[tool.setuptools.packages.find]\nwhere = ["src"]\n''')
    write(module_root / "backend" / "Dockerfile", f'''FROM python:3.14-slim\nWORKDIR /app\nCOPY . .\nRUN python -m pip install .\nUSER 65532\nCMD ["python", "-m", "uvicorn", "{package}.bootstrap.app:app", "--host", "0.0.0.0", "--port", "8000"]\n''')
    write(module_root / "backend" / "tests" / "test_health.py", "def test_placeholder() -> None:\n    assert True\n")
    write(module_root / "frontend" / "manifest.ts", f'''import type {{ PlatformModuleManifest }} from "../../platform-shell/src/app/modules/registry";\n\nexport const {package}Manifest: PlatformModuleManifest = {{\n  id: "{name}",\n  title: "{name}",\n  basePath: "/{name}",\n  requiredPermissions: ["{package}.access"],\n  loadRoutes: () => import("./routes"),\n  navigation: [{{ id: "{name}", title: "{name}", path: "/{name}" }}],\n}};\n''')
    write(module_root / "frontend" / "routes.tsx", f'''export default function {package.title().replace("_", "")}Routes() {{\n  return <main>Модуль {name} готов к реализации.</main>;\n}}\n''')
    write(module_root / "frontend" / "api" / "queryKeys.ts", f'''export const {package}QueryKeys = {{\n  root: ["{name}"] as const,\n}};\n''')
    print(f"Created module scaffold: apps/{name}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: create_module.py <module-name>")
    raise SystemExit(main(sys.argv[1]))

