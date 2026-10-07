"""Create databases for registered generated modules in the shared local PostgreSQL."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def psql(sql: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-At",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-c",
            sql,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    for path in sorted((ROOT / "apps").glob("*/platform/registration.json")):
        registration = json.loads(path.read_text(encoding="utf-8"))
        package = str(registration["backendPackage"])
        if not package.replace("_", "").isalnum():
            raise ValueError(f"Invalid generated database name: {package}")
        if psql(f"SELECT 1 FROM pg_roles WHERE rolname = '{package}'") != "1":
            psql(f"CREATE ROLE \"{package}\" LOGIN PASSWORD '{package}'")
        if psql(f"SELECT 1 FROM pg_database WHERE datname = '{package}'") != "1":
            psql(f'CREATE DATABASE "{package}" OWNER "{package}"')
        print(f"Generated module database ready: {package}")


if __name__ == "__main__":
    main()
