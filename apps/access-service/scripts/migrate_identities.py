from __future__ import annotations

import argparse
import os
from pathlib import Path

from access_service.application.identity_migration import (
    IdentityMigrationConflict,
    migrate_identities,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile legacy Projects and Service Desk users with Access Service",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Analyze only; do not mutate databases")
    mode.add_argument("--apply", action="store_true", help="Apply an unambiguous reconciliation plan")
    parser.add_argument(
        "--projects-database-url",
        default=os.getenv("PROJECTS_DATABASE_URL"),
    )
    parser.add_argument(
        "--service-desk-database-url",
        default=os.getenv("SERVICE_DESK_DATABASE_URL"),
    )
    parser.add_argument(
        "--access-database-url",
        default=os.getenv("ACCESS_DATABASE_URL"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path(os.getenv("IDENTITY_MIGRATION_REPORT_DIR", "outputs/identity-migration")),
    )
    args = parser.parse_args()
    missing = [
        name
        for name, value in (
            ("PROJECTS_DATABASE_URL", args.projects_database_url),
            ("SERVICE_DESK_DATABASE_URL", args.service_desk_database_url),
            ("ACCESS_DATABASE_URL", args.access_database_url),
        )
        if not value
    ]
    if missing:
        parser.error("Missing database URL(s): " + ", ".join(missing))
    return args


def main() -> int:
    args = parse_args()
    try:
        report = migrate_identities(
            projects_database_url=args.projects_database_url,
            service_desk_database_url=args.service_desk_database_url,
            access_database_url=args.access_database_url,
            apply=args.apply,
            report_dir=args.report_dir,
        )
    except IdentityMigrationConflict as exc:
        print(f"Identity migration blocked: {exc}")
        return 2
    summary = report["summary"]
    print(
        f"Identity migration {report['mode']}: identities={summary['identities']} "
        f"conflicts={summary['conflicts']} applied={report['applied']}"
    )
    print(f"Reports: {args.report_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

