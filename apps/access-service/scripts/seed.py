from __future__ import annotations

from sqlalchemy import select

from access_service.application.catalog import ensure_access_catalog
from access_service.domain.models import PlatformUser, UserRoleAssignment
from access_service.infrastructure.database import SessionLocal

USERS = {
    "admin@utmn.ru": ("00000000-0000-0000-0000-000000000001", "Администратор платформы", "platform_admin"),
    "project.manager@utmn.ru": ("00000000-0000-0000-0000-000000000002", "Руководитель проектов", "project_manager"),
    "employee@utmn.ru": ("00000000-0000-0000-0000-000000000003", "Сотрудник", "employee"),
    "sd.manager@utmn.ru": ("00000000-0000-0000-0000-000000000004", "Менеджер Service Desk", "service_desk_manager"),
    "sd.admin@utmn.ru": ("00000000-0000-0000-0000-000000000005", "Администратор Service Desk", "service_desk_admin"),
}


def main() -> None:
    with SessionLocal() as session:
        roles = ensure_access_catalog(session)
        for email, (user_id, name, role_code) in USERS.items():
            user = session.scalar(select(PlatformUser).where(PlatformUser.email == email))
            if user is None:
                user = PlatformUser(id=user_id, external_subject=f"local:{email}", email=email, display_name=name)
                session.add(user)
                session.flush()
            if not any(assignment.role_id == roles[role_code].id for assignment in user.assignments):
                user.assignments.append(UserRoleAssignment(role=roles[role_code]))
        session.commit()
    print("Access Service demo users and RBAC roles are synchronized")


if __name__ == "__main__":
    main()
