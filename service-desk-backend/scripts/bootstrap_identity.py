from __future__ import annotations

import argparse
import os
from typing import Any

from sqlalchemy import create_engine, text

from app.core.database import SessionLocal
from app.modules.access.bootstrap import repair_service_desk_users


DEMO_EMAILS = ("admin@utmn.ru", "manager@utmn.ru", "employee@utmn.ru", "analyst@utmn.ru")


def read_project_demo_users(projects_database_url: str) -> list[dict[str, Any]]:
    engine = create_engine(projects_database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, email, full_name, department, position "
                    "FROM users WHERE lower(email) = ANY(:emails)"
                ).bindparams(emails=list(DEMO_EMAILS))
            ).mappings()
            return [dict(row) for row in rows]
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair local Service Desk demo identity profiles")
    parser.add_argument(
        "--projects-database-url",
        default=os.getenv("PROJECTS_DATABASE_URL"),
        help="Projects SQLAlchemy database URL (or PROJECTS_DATABASE_URL)",
    )
    args = parser.parse_args()
    if not args.projects_database_url:
        raise SystemExit("PROJECTS_DATABASE_URL is required for local identity bootstrap")
    project_users = read_project_demo_users(args.projects_database_url)
    with SessionLocal() as db:
        result = repair_service_desk_users(db, project_users)
        db.commit()
    print(f"Service Desk identity bootstrap: created={result.created} updated={result.updated} skipped={result.skipped}")


if __name__ == "__main__":
    main()
