from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


GENERATOR = Path(__file__).with_name("create_module.py")


def _workspace(root: Path) -> None:
    anchors = {
        "apps/platform-shell/src/app/modules/registry.ts": (
            'import { serviceDeskManifest } from "../../../../service-desk/frontend/manifest";\n'
            "export const platformModules = [\n  serviceDeskManifest,\n];\n"
        ),
        "apps/access-service/src/access_service/application/catalog.py": (
            'MODULES = {\n    "service-desk": "Service Desk",\n}\n'
            'PERMISSIONS = {\n    "platform.admin": "Platform administration",\n}\n'
        ),
        "apps/platform-shell/nginx.conf": (
            "    set $service_desk_backend http://service-desk-backend:8001;\n"
            "    location = /index.html {\n"
        ),
        "compose.yaml": (
            "services:\n  platform-shell:\nvolumes:\n  service_desk_storage:\n"
        ),
        "contracts/generated/package.json": (
            '{"exports": {\n    "./service-desk": "./src/serviceDesk.ts"\n  }}\n'
        ),
    }
    for relative, content in anchors.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _run(root: Path, *args: str, failure: bool = False) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PROM_GENERATOR_ROOT": str(root),
        "PROM_GENERATOR_SKIP_TOOLCHAIN": "1",
    }
    if failure:
        environment["PROM_GENERATOR_INJECT_FAILURE"] = "1"
    return subprocess.run(
        [sys.executable, str(GENERATOR), *args],
        check=False,
        text=True,
        capture_output=True,
        env=environment,
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_create_check_remove_restores_workspace(tmp_path: Path) -> None:
    _workspace(tmp_path)
    before = _snapshot(tmp_path)

    assert _run(tmp_path, "audit-sample-module", "--dry-run").returncode == 0
    assert _snapshot(tmp_path) == before
    assert _run(tmp_path, "audit-sample-module").returncode == 0
    assert _run(tmp_path, "audit-sample-module", "--check").returncode == 0
    assert (tmp_path / "apps/audit-sample-module/backend/alembic/versions/0001_initial.py").is_file()
    assert (tmp_path / "apps/audit-sample-module/frontend/src/theme.css").is_file()
    assert (
        'audit_sample_module_db_data:/var/lib/postgresql"'
        in (tmp_path / "compose.yaml").read_text(encoding="utf-8")
    )
    assert '"react-router-dom": "7.18.3"' in (
        tmp_path / "apps/audit-sample-module/frontend/package.json"
    ).read_text(encoding="utf-8")
    assert "[tool.deptry]" in (
        tmp_path / "apps/audit-sample-module/backend/pyproject.toml"
    ).read_text(encoding="utf-8")
    registration = (tmp_path / "apps/audit-sample-module/platform/registration.json").read_text(
        encoding="utf-8"
    )
    assert '"permission": "audit_sample_module.access"' in registration
    assert '"audience": "audit-sample-module"' in registration
    assert 'createApiClient("/api/audit-sample-module/v1")' in (
        tmp_path / "apps/audit-sample-module/frontend/api/client.ts"
    ).read_text(encoding="utf-8")
    assert (
        "rewrite ^/api/audit-sample-module/v1/(.*)$ /api/v1/$1 break;"
        in (tmp_path / "apps/platform-shell/nginx.conf").read_text(encoding="utf-8")
    )
    assert "audit-sample-module" not in (
        tmp_path / "apps/access-service/src/access_service/application/catalog.py"
    ).read_text(encoding="utf-8")
    assert _run(tmp_path, "audit-sample-module", "--remove").returncode == 0
    assert _snapshot(tmp_path) == before


def test_failure_rolls_back_files_and_registrations(tmp_path: Path) -> None:
    _workspace(tmp_path)
    before = _snapshot(tmp_path)
    result = _run(tmp_path, "rollback-sample", failure=True)
    assert result.returncode != 0
    assert _snapshot(tmp_path) == before


def test_invalid_module_name_is_rejected(tmp_path: Path) -> None:
    _workspace(tmp_path)
    result = _run(tmp_path, "audit_sample")
    assert result.returncode != 0


def test_duplicate_module_is_rejected(tmp_path: Path) -> None:
    _workspace(tmp_path)
    assert _run(tmp_path, "audit-sample-module").returncode == 0
    duplicate = _run(tmp_path, "audit-sample-module")
    assert duplicate.returncode != 0
