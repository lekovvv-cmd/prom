from __future__ import annotations

from sqlalchemy import select

from access_service.application.catalog import ensure_access_catalog
from access_service.application.pilot import PILOT_USERS, stable_user_id
from access_service.domain.models import Module, PlatformUser, UserRoleAssignment
from access_service.infrastructure.database import SessionLocal

def main() -> None:
    with SessionLocal() as session:
        roles = ensure_access_catalog(session)
        service_desk = session.get(Module, "service-desk")
        if service_desk is not None:
            service_desk.is_active = False
        roles["platform_admin"].permissions = [
            permission
            for permission in roles["platform_admin"].permissions
            if not permission.code.startswith("service_desk.")
        ]
        for email, name, role_code in PILOT_USERS:
            user = session.scalar(select(PlatformUser).where(PlatformUser.email == email))
            if user is None:
                user = PlatformUser(
                    id=stable_user_id(email),
                    external_subject=f"pilot:{email}",
                    email=email,
                    display_name=name,
                    department="ТюмГУ",
                    position=name,
                )
                session.add(user)
                session.flush()
            role = roles[role_code]
            if not any(assignment.role_id == role.id for assignment in user.assignments):
                user.assignments.append(UserRoleAssignment(role=role))
        session.commit()
    print("Synchronized 12 PROM pilot accounts and disabled Service Desk access")


if __name__ == "__main__":
    main()
