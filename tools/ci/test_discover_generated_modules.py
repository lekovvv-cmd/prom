from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("discover_generated_modules.py")


def _discovery_module():
    spec = importlib.util.spec_from_file_location("module_discovery", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_module_discovery_returns_an_empty_matrix_without_registrations(
    tmp_path: Path,
) -> None:
    discovery = _discovery_module()
    discovery.ROOT = tmp_path
    (tmp_path / "apps").mkdir()

    assert discovery.generated_modules() == []


def test_generated_module_discovery_reads_registration_metadata(tmp_path: Path) -> None:
    discovery = _discovery_module()
    discovery.ROOT = tmp_path
    registration = tmp_path / "apps" / "documents" / "platform" / "registration.json"
    registration.parent.mkdir(parents=True)
    registration.write_text(
        '{"id":"documents","gatewayPrefix":"/api/documents/v1/"}', encoding="utf-8"
    )

    assert discovery.generated_modules() == [
        {
            "module": "documents",
            "dockerfile": "apps/documents/backend/Dockerfile",
            "health_path": "/api/documents/v1/health/live",
        }
    ]


def test_business_matrix_includes_future_modules_without_a_name_allowlist(tmp_path: Path):
    discovery = _discovery_module()
    discovery.ROOT = tmp_path
    for module, layout in (("projects", "app"), ("documents", "src")):
        backend = tmp_path / "apps" / module / "backend"
        (backend / layout).mkdir(parents=True)
        (backend / "tests").mkdir()
        (backend / "pyproject.toml").write_text(
            f'[project]\nname = "prom-{module}-backend"\n', encoding="utf-8"
        )
    incomplete = tmp_path / "apps" / "incomplete" / "backend"
    incomplete.mkdir(parents=True)
    (incomplete / "pyproject.toml").write_text(
        '[project]\nname = "incomplete"\n', encoding="utf-8"
    )

    assert discovery.business_modules() == [
        {
            "module": name,
            "package": f"prom-{name}-backend",
            "tests": f"apps/{name}/backend/tests",
        }
        for name in ("documents", "projects")
    ]
