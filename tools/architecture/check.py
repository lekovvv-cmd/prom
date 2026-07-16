"""Fast, dependency-free architectural boundary checks for the PROM workspace."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    return [path for pattern in patterns for path in root.rglob(pattern) if "__pycache__" not in path.parts]


def assert_no_match(paths: list[Path], pattern: str, rule: str) -> list[str]:
    violations: list[str] = []
    expression = re.compile(pattern, re.MULTILINE)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if expression.search(text):
            violations.append(f"{rule}: {path.relative_to(ROOT)}")
    return violations


def main() -> int:
    projects = ROOT / "apps" / "projects"
    service_desk = ROOT / "apps" / "service-desk"
    access = ROOT / "apps" / "access-service"
    sdk = ROOT / "packages" / "python" / "platform-sdk"
    violations: list[str] = []

    violations += assert_no_match(files(projects, ("*.py", "*.ts", "*.tsx")), r"service_desk|service-desk", "Projects imports Service Desk")
    violations += assert_no_match(files(service_desk, ("*.py", "*.ts", "*.tsx")), r"projects_database_url|PROJECTS_DATABASE_URL|from\s+projects|import\s+projects", "Service Desk imports Projects")
    violations += assert_no_match(files(access, ("*.py",)), r"from\s+(projects|service_desk)|import\s+(projects|service_desk)", "Access imports a product module")
    violations += assert_no_match(files(sdk, ("*.py",)), r"from\s+(projects|service_desk)|import\s+(projects|service_desk)", "Platform SDK imports a business module")

    for module_root in (projects / "backend" / "app" / "domain", service_desk / "backend" / "app" / "domain"):
        if module_root.exists():
            violations += assert_no_match(files(module_root, ("*.py",)), r"\b(fastapi|sqlalchemy)\b", "Domain imports delivery or ORM infrastructure")

    if violations:
        print("Architecture check failed:", *violations, sep="\n- ")
        return 1
    print("Architecture check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

