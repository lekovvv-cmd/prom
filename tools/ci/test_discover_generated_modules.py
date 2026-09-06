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
