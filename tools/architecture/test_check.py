from __future__ import annotations

import importlib.util
from pathlib import Path


CHECKER = Path(__file__).with_name("check.py")


def _checker():
    spec = importlib.util.spec_from_file_location("architecture_check", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_discovered_business_modules_are_forbidden_from_access_sdk_and_each_other(
    tmp_path: Path, monkeypatch
) -> None:
    checker = _checker()
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    _write(
        tmp_path,
        "apps/access-service/src/access_service/access_projects.py",
        "from projects import something\n",
    )
    _write(
        tmp_path,
        "apps/access-service/src/access_service/access_documents.py",
        "from documents import something\n",
    )
    _write(
        tmp_path,
        "packages/python/platform-sdk/src/platform_sdk/sdk_projects.py",
        "import projects\n",
    )
    _write(tmp_path, "apps/projects/backend/app/modules/project.py", "value = 1\n")
    _write(
        tmp_path,
        "apps/documents/backend/src/documents/domain.py",
        "from projects import something\n",
    )

    modules = checker.discover_business_modules(tmp_path)
    violations = checker.business_import_boundary_violations(tmp_path, modules)

    assert [module.name for module in modules] == ["documents", "projects"]
    assert any(
        violation.startswith("Access imports a business module:")
        and "access_projects.py" in violation
        for violation in violations
    )
    assert any(
        violation.startswith("Platform SDK imports a business module:")
        and "sdk_projects.py" in violation
        for violation in violations
    )
    assert any(
        violation.startswith("Access imports a business module:")
        and "access_documents.py" in violation
        for violation in violations
    )
    assert any(
        violation.startswith("documents imports business module projects:")
        for violation in violations
    )
