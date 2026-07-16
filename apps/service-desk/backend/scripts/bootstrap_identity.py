"""Seed local Service Desk profiles from the platform demo identity contract.

This script intentionally has no Projects database URL and performs no
cross-module SQL reads.  Production users are synchronized through Access
Service sessions; the static records below are only the local SSO-mock fixture.
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.modules.access.bootstrap import repair_service_desk_users


DEMO_PLATFORM_USERS = (
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@utmn.ru",
        "full_name": "Администратор ШПИУ",
        "department": "ШПИУ",
        "position": "Администратор платформы",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "project.manager@utmn.ru",
        "full_name": "Руководитель проекта",
        "department": "ШПИУ",
        "position": "Руководитель проектных инициатив",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "employee@utmn.ru",
        "full_name": "Сотрудник ШПИУ",
        "department": "ШПИУ",
        "position": "Методист проектных программ",
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "email": "sd.manager@utmn.ru",
        "full_name": "Менеджер Service Desk",
        "department": "Service Desk",
        "position": "Менеджер Service Desk",
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "email": "sd.admin@utmn.ru",
        "full_name": "Администратор Service Desk",
        "department": "Service Desk",
        "position": "Администратор Service Desk",
    },
)


def main() -> None:
    with SessionLocal() as db:
        result = repair_service_desk_users(db, DEMO_PLATFORM_USERS)
        db.commit()
    print(f"Service Desk local identity bootstrap: created={result.created} updated={result.updated} skipped={result.skipped}")


if __name__ == "__main__":
    main()
