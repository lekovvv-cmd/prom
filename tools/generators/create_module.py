"""Create and register a production-shaped PROM bounded-context module."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(os.getenv("PROM_GENERATOR_ROOT", Path(__file__).resolve().parents[2])).resolve()
SDK_SOURCE = Path(__file__).resolve().parents[2] / "packages" / "python" / "platform-sdk" / "src"
CONVENTION_SPEC = importlib.util.spec_from_file_location(
    "prom_module_conventions", SDK_SOURCE / "platform_sdk" / "modules.py"
)
if CONVENTION_SPEC is None or CONVENTION_SPEC.loader is None:
    raise RuntimeError("PROM module conventions are unavailable")
_conventions = importlib.util.module_from_spec(CONVENTION_SPEC)
CONVENTION_SPEC.loader.exec_module(_conventions)
module_access_permission = _conventions.module_access_permission
module_python_package = _conventions.module_python_package
module_token_audience = _conventions.module_token_audience
validate_module_id = _conventions.validate_module_id


def _render(value: str) -> str:
    return value.strip() + "\n"


@dataclass
class ChangeSet:
    root: Path
    dry_run: bool = False
    backups: dict[Path, bytes | dict[str, bytes] | None] = field(default_factory=dict)

    def remember(self, path: Path) -> None:
        if path not in self.backups:
            if path.is_dir():
                self.backups[path] = {
                    item.relative_to(path).as_posix(): item.read_bytes()
                    for item in path.rglob("*")
                    if item.is_file()
                }
            else:
                self.backups[path] = path.read_bytes() if path.exists() else None

    def write(self, path: Path, content: str) -> None:
        self.remember(path)
        if self.dry_run:
            print(f"CREATE {path.relative_to(self.root)}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(path, content.encode("utf-8"))

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        temporary = path.with_name(f".{path.name}.{os.getpid()}.prom-generator.tmp")
        try:
            temporary.write_bytes(payload)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def replace(self, path: Path, old: str, new: str) -> None:
        payload = path.read_bytes()
        newline = "\r\n" if b"\r\n" in payload else "\n"
        old_bytes = old.replace("\n", newline).encode("utf-8")
        new_bytes = new.replace("\n", newline).encode("utf-8")
        if old_bytes not in payload:
            raise RuntimeError(f"Registration anchor missing in {path.relative_to(self.root)}")
        self.remember(path)
        if self.dry_run:
            print(f"EDIT   {path.relative_to(self.root)}")
            return
        self._atomic_write(path, payload.replace(old_bytes, new_bytes, 1))

    def rollback(self) -> None:
        if self.dry_run:
            return
        for path, content in reversed(list(self.backups.items())):
            if content is None:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
            elif isinstance(content, bytes):
                path.parent.mkdir(parents=True, exist_ok=True)
                self._atomic_write(path, content)
            else:
                shutil.rmtree(path, ignore_errors=True)
                for relative, payload in content.items():
                    target = path / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    self._atomic_write(target, payload)


def _validate_name(name: str) -> None:
    validate_module_id(name)


def _module_values(name: str) -> tuple[str, str, str, int]:
    name = validate_module_id(name)
    package = module_python_package(name)
    component = "".join(part.title() for part in package.split("_"))
    variable = package.split("_")[0] + "".join(part.title() for part in package.split("_")[1:])
    port = 8100 + (zlib.crc32(name.encode("utf-8")) % 800)
    return package, component, variable, port


def _files(name: str) -> dict[Path, str]:
    package, component, variable, port = _module_values(name)
    module = Path("apps") / name
    permission = module_access_permission(name)
    registration = {
        "id": name,
        "title": component,
        "permission": permission,
        "audience": module_token_audience(name),
        "backendPackage": package,
        "backendService": f"{name}-backend",
        "backendPort": port,
        "gatewayPrefix": f"/api/{name}/v1/",
        "openapiFile": f"{name}.openapi.json",
        "generatedFile": f"{variable}.ts",
    }
    return {
        module / "README.md": _render(
            f"""
# {component}

Generated PROM bounded context. Domain behavior belongs in `backend/src/{package}/domain`;
transport adapters must call application use cases through an explicit unit of work.

Permission: `{permission}`. API prefix: `/api/{name}/v1/`.
"""
        ),
        module / "platform" / "registration.json": json.dumps(registration, indent=2) + "\n",
        module / "backend" / "src" / package / "__init__.py": f'"""PROM {component} module."""\n',
        module / "backend" / "src" / package / "config.py": _render(
            f"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="{package.upper()}_", extra="ignore")
    database_url: str = "postgresql+psycopg://{package}:{package}@{name}-db:5432/{package}"
    access_jwks_url: str = "http://access-service:8002/.well-known/jwks.json"
    access_token_issuer: str = "prom-access"
    access_token_audience: str = "{module_token_audience(name)}"
    access_jwks_cache_ttl_seconds: int = 300
    access_jwks_stale_if_error_seconds: int = 3600
    access_clock_skew_seconds: int = 30


settings = Settings()
"""
        ),
        module / "backend" / "src" / package / "database.py": _render(
            f"""
from collections.abc import Generator

from platform_sdk.database import DatabasePoolConfig, create_platform_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_platform_engine(settings.database_url, DatabasePoolConfig(application_name="prom-{name}-api"))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                session.rollback()
"""
        ),
        module / "backend" / "src" / package / "errors.py": _render(
            """
from platform_sdk.error_types import EntityNotFound, InvalidRequest

__all__ = ["EntityNotFound", "InvalidRequest"]
"""
        ),
        module / "backend" / "src" / package / "security.py": _render(
            f'''
from functools import lru_cache
from typing import Annotated

from fastapi import Header, HTTPException, status
from platform_sdk.auth import CachedJwksVerifier, CurrentPrincipal

from .config import settings


@lru_cache(maxsize=1)
def _platform_verifier() -> CachedJwksVerifier:
    return CachedJwksVerifier(
        jwks_url=settings.access_jwks_url,
        audience=settings.access_token_audience,
        issuer=settings.access_token_issuer,
        cache_ttl_seconds=settings.access_jwks_cache_ttl_seconds,
        stale_if_error_seconds=settings.access_jwks_stale_if_error_seconds,
        clock_skew_seconds=settings.access_clock_skew_seconds,
    )


def require_module_access(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentPrincipal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        principal = _platform_verifier().verify(authorization.split(" ", maxsplit=1)[1])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid platform token") from exc
    if not principal.has_permission("{permission}"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return principal
'''
        ),
        module / "backend" / "src" / package / "unit_of_work.py": _render(
            """
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork

__all__ = ["SqlAlchemyUnitOfWork"]
"""
        ),
        module / "backend" / "src" / package / "platform_events.py": _render(
            """
from platform_sdk.outbox import AuditEventMixin, OutboxEventMixin
from .database import Base


class AuditEvent(AuditEventMixin, Base):
    __tablename__ = "audit_events"


class OutboxEvent(OutboxEventMixin, Base):
    __tablename__ = "outbox_events"
"""
        ),
        module / "backend" / "src" / package / "bootstrap" / "__init__.py": "",
        module / "backend" / "src" / package / "bootstrap" / "app.py": _render(
            f"""
from fastapi import Depends, FastAPI
from platform_sdk.auth import CurrentPrincipal
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_session
from ..security import require_module_access


def create_app() -> FastAPI:
    app = FastAPI(title="PROM {component}", version="1.0.0")

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {{"status": "live"}}

    @app.get("/health/ready", tags=["health"])
    def ready(db: Session = Depends(get_session)) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        return {{"status": "ready"}}

    @app.get("/api/v1/me", tags=["identity"])
    def me(principal: CurrentPrincipal = Depends(require_module_access)) -> dict[str, str]:
        return {{"user_id": principal.user_id, "module_id": "{name}"}}

    return app


app = create_app()
"""
        ),
        module / "backend" / "alembic.ini": _render(
            f"""
[alembic]
script_location = alembic
prepend_sys_path = src
sqlalchemy.url = postgresql+psycopg://{package}:{package}@localhost:5432/{package}
"""
        ),
        module / "backend" / "alembic" / "env.py": _render(
            f"""
from alembic import context
from sqlalchemy import engine_from_config, pool

from {package}.database import Base
from {package}.config import settings
from {package} import platform_events  # noqa: F401

target_metadata = Base.metadata
context.config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    context.configure(url=context.config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(context.config.get_section(context.config.config_ini_section) or {{}}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
"""
        ),
        module / "backend" / "alembic" / "script.py.mako": "${up_revision} = ${repr(up_revision)}\n",
        module / "backend" / "alembic" / "versions" / "0001_initial.py": _render(
            f'''"""Initial {component} platform tables."""

from alembic import op

from {package}.database import Base
from {package} import platform_events  # noqa: F401

revision = "{package}_0001"
down_revision = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("audit_events")
'''
        ),
        module / "backend" / "tests" / "test_health.py": _render(
            f"""
from fastapi.testclient import TestClient
from platform_sdk.auth import CurrentPrincipal

from {package}.bootstrap.app import create_app
from {package} import security


def test_liveness() -> None:
    assert TestClient(create_app()).get("/health/live").json() == {{"status": "live"}}


def test_module_endpoint_requires_the_canonical_access_permission(monkeypatch) -> None:
    class Verifier:
        def verify(self, _token: str) -> CurrentPrincipal:
            return CurrentPrincipal(
                user_id="user-1", external_subject=None, email=None, display_name=None,
                permissions=frozenset({{"{permission}"}}), audiences=frozenset({{"{module_token_audience(name)}"}}),
            )

    monkeypatch.setattr(security, "_platform_verifier", lambda: Verifier())
    client = TestClient(create_app())
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/me", headers={{"Authorization": "Bearer valid"}}).json() == {{"user_id": "user-1", "module_id": "{name}"}}
"""
        ),
        module / "backend" / "tests" / "conftest.py": _render(
            """
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
"""
        ),
        module / "backend" / "pyproject.toml": _render(
            f"""
[build-system]
requires = ["setuptools>=82"]
build-backend = "setuptools.build_meta"

[project]
name = "prom-{name}-backend"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
  "alembic>=1.18,<2",
  "fastapi>=0.136,<0.137",
  "prom-platform-sdk>=0.1.0",
  "psycopg[binary]>=3.3,<4",
  "pydantic-settings>=2.13,<3",
  "sqlalchemy>=2.0,<3",
  "uvicorn[standard]>=0.41,<1",
]

[project.optional-dependencies]
dev = ["httpx>=0.28,<1", "pytest>=9,<10", "ruff>=0.15,<1"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.deptry]
known_first_party = ["{package}"]
package_module_name_map = {{ prom-platform-sdk = "platform_sdk" }}
optional_dependencies_dev_groups = ["dev"]
# Alembic, the DB driver and Uvicorn are executed by the runtime rather than
# imported from application modules.  TestClient pulls httpx transitively;
# pytest and Ruff are runner/tool dependencies.
per_rule_ignores = {{ DEP002 = ["alembic", "psycopg", "uvicorn", "httpx", "pytest", "ruff"] }}

[tool.uv.sources]
prom-platform-sdk = {{ workspace = true }}
"""
        ),
        module / "backend" / "Dockerfile": _render(
            f"""
FROM ghcr.io/astral-sh/uv:0.11.29 AS uv
FROM python:3.14.6-slim AS runtime
COPY --from=uv /uv /uvx /bin/
WORKDIR /workspace
ENV PATH="/workspace/.venv/bin:$PATH" UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
COPY packages/python/platform-sdk packages/python/platform-sdk
COPY apps apps
RUN uv sync --locked --no-dev --package prom-{name}-backend
WORKDIR /workspace/apps/{name}/backend
USER 65532
EXPOSE {port}
CMD ["python", "-m", "uvicorn", "{package}.bootstrap.app:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
        ),
        module / "frontend" / "package.json": json.dumps(
            {
                "name": f"@prom/{name}-frontend",
                "private": True,
                "type": "module",
                "dependencies": {
                    "@prom/api-client": "0.1.0",
                    "@prom/platform-contracts": "0.1.0",
                    "@prom/ui": "0.1.0",
                },
                "peerDependencies": {"react": "19.2.7", "react-router-dom": "7.18.3"},
                "devDependencies": {"vitest": "4.1.9"},
            },
            indent=2,
        )
        + "\n",
        module / "frontend" / "manifest.ts": _render(
            f"""
import type {{ PlatformModuleManifest }} from "@prom/platform-contracts";

export const {variable}Manifest: PlatformModuleManifest = {{
  id: "{name}",
  title: "{component}",
  description: "PROM {component} module",
  basePath: "/{name}",
  routePrefixes: ["/{name}"],
  requiredPermissions: ["{permission}"],
  loadRoutes: () => import("./routes"),
  navigation: [{{ id: "{name}", title: "{component}", path: "/{name}", requiredPermissions: ["{permission}"] }}],
}};
"""
        ),
        module / "frontend" / "routes.tsx": _render(
            f"""
import {{ Route, Routes }} from "react-router-dom";
import {{ {component}Page }} from "./src/{component}Page";
import "./src/theme.css";

export default function {component}Routes() {{
  return <Routes><Route path="/{name}" element={{<{component}Page />}} /></Routes>;
}}
"""
        ),
        module / "frontend" / "src" / f"{component}Page.tsx": _render(
            f"""
export function {component}Page() {{
  return <main className="mx-auto max-w-5xl p-6"><h1 className="text-2xl font-semibold">{component}</h1><p className="mt-2 text-slate-600">Module scaffold is ready.</p></main>;
}}
"""
        ),
        module / "frontend" / "src" / f"{component}Page.test.tsx": _render(
            f"""
import {{ describe, expect, it }} from "vitest";
import {{ {component}Page }} from "./{component}Page";

describe("{component}Page", () => {{
  it("exports the example page", () => expect({component}Page).toBeTypeOf("function"));
}});
"""
        ),
        module / "frontend" / "src" / "theme.css": '@import "tailwindcss";\n@theme { --color-brand-600: #2563eb; }\n',
        module / "frontend" / "api" / "client.ts": _render(
            f"""
import {{ createApiClient }} from "@prom/api-client";

export const {variable}Api = createApiClient("/api/{name}/v1");
"""
        ),
        module / "frontend" / "api" / "queryKeys.ts": f'export const {variable}QueryKeys = {{ root: ["{name}"] as const }};\n',
    }


def _register(change: ChangeSet, name: str) -> None:
    package, component, variable, port = _module_values(name)
    registry = ROOT / "apps/platform-shell/src/app/modules/registry.ts"
    change.replace(
        registry,
        'import { serviceDeskManifest } from "../../../../service-desk/frontend/manifest";\n',
        'import { serviceDeskManifest } from "../../../../service-desk/frontend/manifest";\n'
        f'import {{ {variable}Manifest }} from "../../../../{name}/frontend/manifest";\n',
    )
    change.replace(registry, "  serviceDeskManifest,\n", f"  serviceDeskManifest,\n  {variable}Manifest,\n")

    nginx = ROOT / "apps/platform-shell/nginx.conf"
    change.replace(nginx, "    set $service_desk_backend http://service-desk-backend:8001;\n", f"    set $service_desk_backend http://service-desk-backend:8001;\n    set ${package}_backend http://{name}-backend:{port};\n")
    location = f'''    location /api/{name}/v1/ {{
        rewrite ^/api/{name}/v1/(.*)$ /api/v1/$1 break;
        proxy_pass ${package}_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Request-ID $prom_request_id;
        proxy_set_header X-Correlation-ID $prom_correlation_id;
    }}

'''
    change.replace(nginx, "    location = /index.html {\n", location + "    location = /index.html {\n")

    compose = ROOT / "compose.yaml"
    services = f'''  {name}-db:
    image: postgres:18.3-alpine
    profiles: ["{name}", "full"]
    environment:
      POSTGRES_USER: {package}
      POSTGRES_PASSWORD: ${{{package.upper()}_DB_PASSWORD:-{package}}}
      POSTGRES_DB: {package}
    volumes: ["{package}_db_data:/var/lib/postgresql"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {package} -d {package}"]
      interval: 5s
      timeout: 3s
      retries: 20

  {name}-migrate:
    build:
      context: .
      dockerfile: apps/{name}/backend/Dockerfile
    profiles: ["{name}", "full"]
    environment:
      {package.upper()}_DATABASE_URL: postgresql+psycopg://{package}:${{{package.upper()}_DB_PASSWORD:-{package}}}@{name}-db:5432/{package}
    command: ["alembic", "upgrade", "head"]
    depends_on:
      {name}-db: {{ condition: service_healthy }}

  {name}-backend:
    build:
      context: .
      dockerfile: apps/{name}/backend/Dockerfile
    profiles: ["{name}", "full"]
    environment:
      {package.upper()}_DATABASE_URL: postgresql+psycopg://{package}:${{{package.upper()}_DB_PASSWORD:-{package}}}@{name}-db:5432/{package}
      {package.upper()}_ACCESS_JWKS_URL: ${{{package.upper()}_ACCESS_JWKS_URL:-http://access-service:8002/.well-known/jwks.json}}
      {package.upper()}_ACCESS_TOKEN_ISSUER: ${{{package.upper()}_ACCESS_TOKEN_ISSUER:-prom-access}}
      {package.upper()}_ACCESS_TOKEN_AUDIENCE: {module_token_audience(name)}
    depends_on:
      {name}-migrate: {{ condition: service_completed_successfully }}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}/health/live')"]
      interval: 10s
      timeout: 3s
      retries: 10

'''
    change.replace(compose, "  platform-shell:\n", services + "  platform-shell:\n")
    change.replace(compose, "  service_desk_storage:\n", f"  service_desk_storage:\n  {package}_db_data:\n")
    generated_package = ROOT / "contracts/generated/package.json"
    change.replace(
        generated_package,
        '    "./service-desk": "./src/serviceDesk.ts"\n',
        f'    "./service-desk": "./src/serviceDesk.ts",\n    "./{name}": "./src/{variable}.ts"\n',
    )


def _unregister(change: ChangeSet, name: str) -> None:
    registration_path = ROOT / "apps" / name / "platform" / "registration.json"
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    package = str(registration["backendPackage"])
    variable = Path(str(registration["generatedFile"])).stem
    port = int(registration["backendPort"])

    registry = ROOT / "apps/platform-shell/src/app/modules/registry.ts"
    change.replace(registry, f'import {{ {variable}Manifest }} from "../../../../{name}/frontend/manifest";\n', "")
    change.replace(registry, f"  {variable}Manifest,\n", "")
    nginx = ROOT / "apps/platform-shell/nginx.conf"
    change.replace(nginx, f"    set ${package}_backend http://{name}-backend:{port};\n", "")
    start = f"    location /api/{name}/v1/ {{\n"
    text = nginx.read_text(encoding="utf-8")
    end_at = text.index("    location = /index.html {", text.index(start))
    change.replace(nginx, text[text.index(start) : end_at], "")
    compose = ROOT / "compose.yaml"
    text = compose.read_text(encoding="utf-8")
    start = f"  {name}-db:\n"
    end_at = text.index("  platform-shell:\n", text.index(start))
    change.replace(compose, text[text.index(start) : end_at], "")
    change.replace(compose, f"  {package}_db_data:\n", "")
    generated_package = ROOT / "contracts/generated/package.json"
    change.replace(
        generated_package,
        f'    "./service-desk": "./src/serviceDesk.ts",\n    "./{name}": "./src/{variable}.ts"\n',
        '    "./service-desk": "./src/serviceDesk.ts"\n',
    )
    for path in (
        ROOT / "contracts/openapi" / str(registration["openapiFile"]),
        ROOT / "contracts/generated/src" / str(registration["generatedFile"]),
    ):
        change.remember(path)
        if change.dry_run:
            print(f"REMOVE {path.relative_to(ROOT)}")
        else:
            path.unlink(missing_ok=True)

    module_root = ROOT / "apps" / name
    change.remember(module_root)
    if change.dry_run:
        print(f"REMOVE {module_root.relative_to(ROOT)}")
    else:
        shutil.rmtree(module_root)


def check(name: str) -> int:
    required = list(_files(name))
    missing = [str(path) for path in required if not (ROOT / path).is_file()]
    registration = ROOT / "apps" / name / "platform" / "registration.json"
    if registration.is_file():
        values = json.loads(registration.read_text(encoding="utf-8"))
        needles = {
            ROOT / "apps/platform-shell/src/app/modules/registry.ts": f'../../../../{name}/frontend/manifest',
            ROOT / "apps" / name / "frontend" / "manifest.ts": str(values["permission"]),
            ROOT / "apps/platform-shell/nginx.conf": str(values["gatewayPrefix"]),
            ROOT / "compose.yaml": f"  {name}-backend:",
        }
        for path, needle in needles.items():
            if needle not in path.read_text(encoding="utf-8"):
                missing.append(f"registration {needle} in {path.relative_to(ROOT)}")
        for path in (
            ROOT / "contracts/openapi" / str(values["openapiFile"]),
            ROOT / "contracts/generated/src" / str(values["generatedFile"]),
        ):
            if not path.is_file():
                missing.append(str(path.relative_to(ROOT)))
    if missing:
        print("Module check failed:", *missing, sep="\n- ")
        return 1
    print(f"Module scaffold is complete and registered: {name}")
    return 0


def _tool(name: str) -> str:
    configured = os.getenv(f"PROM_{name.upper()}")
    if configured and Path(configured).is_file():
        return configured
    candidates = (f"{name}.cmd", f"{name}.exe", name) if os.name == "nt" else (name,)
    for candidate in candidates:
        if executable := shutil.which(candidate):
            return executable
    local = Path.home() / ".local" / "bin" / (f"{name}.exe" if os.name == "nt" else name)
    if local.is_file():
        return str(local)
    raise FileNotFoundError(f"Required tool is not available: {name}")


def _refresh_workspace(change: ChangeSet, name: str) -> None:
    if change.dry_run:
        print("RUN    uv lock")
        print("RUN    npm install --package-lock-only --ignore-scripts")
        print("RUN    npm run generate:contracts")
        return
    registration = json.loads(
        (ROOT / "apps" / name / "platform" / "registration.json").read_text(
            encoding="utf-8"
        )
    )
    openapi_path = ROOT / "contracts/openapi" / str(registration["openapiFile"])
    generated_path = ROOT / "contracts/generated/src" / str(
        registration["generatedFile"]
    )
    if os.getenv("PROM_GENERATOR_SKIP_TOOLCHAIN"):
        change.write(
            openapi_path,
            json.dumps(
                {
                    "openapi": "3.1.0",
                    "info": {"title": name, "version": "1.0.0"},
                    "paths": {},
                },
                indent=2,
            )
            + "\n",
        )
        change.write(
            generated_path,
            "// Generated smoke-test placeholder.\nexport interface paths {}\n",
        )
        return

    state_root = ROOT / "apps" / name / "platform" / ".generator-state"
    state_root.mkdir(parents=True, exist_ok=True)
    change._atomic_write(state_root / "uv.lock", (ROOT / "uv.lock").read_bytes())
    change._atomic_write(
        state_root / "package-lock.json",
        (ROOT / "package-lock.json").read_bytes(),
    )
    for path in (ROOT / "uv.lock", ROOT / "package-lock.json", openapi_path, generated_path):
        change.remember(path)
    commands = (
        ([_tool("uv"), "lock"], "uv lock"),
        (
            [
                _tool("uv"),
                "sync",
                "--locked",
                "--all-packages",
                "--all-extras",
            ],
            "workspace dependency sync",
        ),
        (
            [
                _tool("npm"),
                "install",
                "--package-lock-only",
                "--ignore-scripts",
            ],
            "npm install",
        ),
        (
            [_tool("npm"), "run", "generate:contracts"],
            "contract generation",
        ),
    )
    for command, label in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"{label} failed:\n{result.stderr or result.stdout}")


def _refresh_locks(change: ChangeSet, name: str) -> None:
    if change.dry_run or os.getenv("PROM_GENERATOR_SKIP_TOOLCHAIN"):
        return
    state_root = ROOT / "apps" / name / "platform" / ".generator-state"
    for file_name in ("uv.lock", "package-lock.json"):
        stored = state_root / file_name
        if not stored.is_file():
            raise RuntimeError(f"Generator state is missing: {stored.relative_to(ROOT)}")
        target = ROOT / file_name
        change.remember(target)
        change._atomic_write(target, stored.read_bytes())


def create(name: str, *, dry_run: bool) -> int:
    module_root = ROOT / "apps" / name
    if module_root.exists():
        raise FileExistsError(f"Module already exists: {module_root}")
    change = ChangeSet(ROOT, dry_run=dry_run)
    try:
        change.remember(module_root)
        for relative, content in _files(name).items():
            change.write(ROOT / relative, content)
        _register(change, name)
        _refresh_workspace(change, name)
        if os.getenv("PROM_GENERATOR_INJECT_FAILURE"):
            raise RuntimeError("Injected generator failure")
    except BaseException:
        change.rollback()
        raise
    print(f"{'Would create' if dry_run else 'Created'} module scaffold: apps/{name}")
    print("Verify: uv lock && npm install --package-lock-only && npm run check:contracts")
    print(f"Verify: python tools/generators/create_module.py --check {name}")
    return 0


def remove(name: str, *, dry_run: bool) -> int:
    if not (ROOT / "apps" / name / "platform" / "registration.json").is_file():
        raise FileNotFoundError(f"Generated module registration not found: {name}")
    change = ChangeSet(ROOT, dry_run=dry_run)
    try:
        _refresh_locks(change, name)
        _unregister(change, name)
    except BaseException:
        change.rollback()
        raise
    print(f"{'Would remove' if dry_run else 'Removed'} generated module: {name}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--check", action="store_true")
    operation.add_argument("--remove", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    _validate_name(args.name)
    if args.check:
        return check(args.name)
    if args.remove:
        return remove(args.name, dry_run=args.dry_run)
    return create(args.name, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
