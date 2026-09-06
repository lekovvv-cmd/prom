"""Emit the generated-module CI matrix from runtime registration metadata."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def generated_modules() -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    for registration_path in sorted((ROOT / "apps").glob("*/platform/registration.json")):
        registration = json.loads(registration_path.read_text(encoding="utf-8"))
        module = str(registration["id"])
        modules.append(
            {
                "module": module,
                "dockerfile": f"apps/{module}/backend/Dockerfile",
                "health_path": f"{registration['gatewayPrefix']}health/live",
            }
        )
    return modules


def business_modules() -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    for backend in sorted((ROOT / "apps").glob("*/backend")):
        pyproject = backend / "pyproject.toml"
        tests = backend / "tests"
        if not pyproject.is_file() or not tests.is_dir():
            continue
        package = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
        modules.append(
            {
                "module": backend.parent.name,
                "package": package,
                "tests": tests.relative_to(ROOT).as_posix(),
            }
        )
    return modules


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--business", action="store_true")
    args = parser.parse_args()
    modules = business_modules() if args.business else generated_modules()
    print(json.dumps({"include": modules}, separators=(",", ":")))


if __name__ == "__main__":
    main()
