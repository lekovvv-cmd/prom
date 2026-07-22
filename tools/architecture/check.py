"""Fast, dependency-free architectural boundary checks for the PROM workspace."""

from __future__ import annotations

import re
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


def assert_contains(path: Path, pattern: str, rule: str) -> list[str]:
    if not path.is_file():
        return [f"{rule}: missing {path.relative_to(ROOT)}"]
    if re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE):
        return []
    return [f"{rule}: {path.relative_to(ROOT)}"]


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

    business_roots = (
        projects / "backend" / "app" / "modules",
        service_desk / "backend" / "app" / "modules",
        access / "src" / "access_service" / "application",
        access / "src" / "access_service" / "domain",
    )
    for module_root in business_roots:
        violations += assert_no_match(
            files(module_root, ("*.py",)),
            r"^\s*(?:from\s+fastapi\b|import\s+fastapi\b)",
            "Business code imports FastAPI transport",
        )

    repository_files = files(projects / "backend", ("*repository.py",))
    repository_files += files(service_desk / "backend", ("*repository.py",))
    repository_files += files(access, ("*repository.py",))
    violations += assert_no_match(
        repository_files,
        r"\.(?:commit|rollback)\(",
        "Repository owns a transaction boundary",
    )

    dockerfiles = (
        projects / "backend" / "Dockerfile",
        service_desk / "backend" / "Dockerfile",
        access / "Dockerfile",
    )
    for dockerfile in dockerfiles:
        violations += assert_contains(
            dockerfile,
            r"ghcr\.io/astral-sh/uv:0\.11\.29",
            "Backend image must pin uv",
        )
        violations += assert_contains(
            dockerfile,
            r"uv sync --locked --no-dev --package",
            "Backend runtime dependencies must use the lockfile without dev extras",
        )
        violations += assert_no_match(
            [dockerfile],
            r"\bpip install\b",
            "Backend image bypasses the uv lockfile",
        )

    violations += assert_contains(ROOT / "uv.lock", r"^version = \d+", "Committed uv lockfile is required")
    violations += assert_contains(
        ROOT / ".github" / "workflows" / "ci.yml",
        r"uv lock --check",
        "CI must reject a stale Python lockfile",
    )
    violations += assert_no_match(
        [ROOT / ".github" / "workflows" / "ci.yml"],
        r"\bpip install\b",
        "CI bypasses the uv workspace",
    )
    violations += assert_contains(
        ROOT / "packages" / "frontend" / "platform-contracts" / "src" / "index.ts",
        r"export type PlatformModuleManifest",
        "Shared module manifest contract is required",
    )
    violations += assert_contains(
        ROOT / "packages" / "frontend" / "ui" / "package.json",
        r'"name": "@prom/ui"',
        "Shared frontend UI package is required",
    )
    manifests = [
        projects / "frontend" / "manifest.ts",
        service_desk / "frontend" / "manifest.ts",
    ]
    violations += assert_no_match(
        manifests,
        r"platform-shell/src",
        "Module manifest imports platform-shell internals",
    )
    for manifest in manifests:
        violations += assert_contains(
            manifest,
            r"routePrefixes\s*:",
            "Module manifest must declare every URL prefix it owns",
        )
    violations += assert_contains(
        ROOT / "apps" / "platform-shell" / "src" / "app" / "routes" / "AppRouter.tsx",
        r"getPlatformModuleForPath",
        "Platform shell must dispatch routes through module manifests",
    )
    for frontend_root in (
        projects / "frontend",
        service_desk / "frontend",
    ):
        violations += assert_no_match(
            files(frontend_root, ("*.ts", "*.tsx")),
            r"platform-shell/src",
            "Product frontend imports platform-shell internals",
        )
    shared_frontend = ROOT / "packages" / "frontend"
    violations += assert_no_match(
        files(shared_frontend, ("*.ts", "*.tsx")),
        r"(?:apps[/\\](?:projects|service-desk)|(?:projects|service-desk)[/\\]frontend)",
        "Shared frontend package imports a product module",
    )
    shared_transport = shared_frontend / "api-client" / "src" / "client.ts"
    violations += assert_no_match(
        [shared_transport],
        r"(?i)\b(?:project|ticket|sla|report)s?\b",
        "Shared API transport contains product vocabulary",
    )
    violations += assert_no_match(
        files(shared_frontend / "api-client", ("*.ts", "*.tsx"))
        + files(shared_frontend / "auth", ("*.ts", "*.tsx")),
        r"(?i)localStorage[^\n]*(?:token|jwt)|shpiu_project_showcase_token",
        "Privileged browser token is persisted in localStorage",
    )
    legacy_shell_ui = ROOT / "apps" / "platform-shell" / "src" / "shared" / "ui"
    if legacy_shell_ui.exists():
        violations.append(
            f"Reusable UI still belongs to the shell: {legacy_shell_ui.relative_to(ROOT)}"
        )
    shell_product_roots = (
        ROOT / "apps" / "platform-shell" / "src" / "entities",
        ROOT / "apps" / "platform-shell" / "src" / "features",
        ROOT / "apps" / "platform-shell" / "src" / "widgets",
    )
    for shell_product_root in shell_product_roots:
        owned_files = files(shell_product_root, ("*.ts", "*.tsx"))
        if owned_files:
            violations.extend(
                f"Product code still belongs to the shell: {path.relative_to(ROOT)}"
                for path in owned_files
            )

    if violations:
        print("Architecture check failed:", *violations, sep="\n- ")
        return 1
    print("Architecture check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
