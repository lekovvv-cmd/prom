from __future__ import annotations

from sqlalchemy import select

from access_service.domain.models import Module, Permission, PlatformUser, Role, UserRoleAssignment
from access_service.infrastructure.database import SessionLocal


PERMISSIONS = {
    "platform.admin": "Platform administration",
    "projects.access": "Access Projects",
    "projects.create": "Create projects",
    "projects.update_own": "Update own projects",
    "projects.update_any": "Update any project",
    "projects.manage_members": "Manage project members",
    "projects.manage_responses": "Manage project responses",
    "projects.manage_tasks": "Manage project tasks",
    "projects.manage_reports": "Manage project reports",
    "service_desk.access": "Access Service Desk",
    "service_desk.assign": "Assign Service Desk tickets",
    "service_desk.approve": "Approve Service Desk tickets",
    "service_desk.manage_catalog": "Manage Service Desk catalog",
    "service_desk.manage_sla": "Manage Service Desk SLA",
    "service_desk.manage_access": "Manage Service Desk access",
}

ROLES = {
    "employee": ("Сотрудник", {"projects.access", "service_desk.access"}),
    "project_manager": ("Руководитель проектов", {"projects.access", "projects.create", "projects.update_own", "projects.manage_members", "projects.manage_responses", "projects.manage_tasks", "projects.manage_reports"}),
    "service_desk_manager": ("Менеджер Service Desk", {"service_desk.access", "service_desk.assign", "service_desk.approve"}),
    "service_desk_admin": ("Администратор Service Desk", {"service_desk.access", "service_desk.assign", "service_desk.approve", "service_desk.manage_catalog", "service_desk.manage_sla", "service_desk.manage_access"}),
    "platform_admin": ("Администратор платформы", set(PERMISSIONS)),
}

USERS = {
    "admin@utmn.ru": ("00000000-0000-0000-0000-000000000001", "Администратор платформы", "platform_admin"),
    "project.manager@utmn.ru": ("00000000-0000-0000-0000-000000000002", "Руководитель проектов", "project_manager"),
    "employee@utmn.ru": ("00000000-0000-0000-0000-000000000003", "Сотрудник", "employee"),
    "sd.manager@utmn.ru": ("00000000-0000-0000-0000-000000000004", "Менеджер Service Desk", "service_desk_manager"),
    "sd.admin@utmn.ru": ("00000000-0000-0000-0000-000000000005", "Администратор Service Desk", "service_desk_admin"),
}


def main() -> None:
    with SessionLocal() as session:
        for module_id, title in (("projects", "Projects"), ("service-desk", "Service Desk")):
            if session.get(Module, module_id) is None:
                session.add(Module(id=module_id, title=title))
        session.flush()
        for code, title in PERMISSIONS.items():
            if session.scalar(select(Permission).where(Permission.code == code)) is None:
                session.add(Permission(code=code, title=title, module_id="service-desk" if code.startswith("service_desk") else "projects" if code.startswith("projects") else None))
        session.flush()
        permissions = {permission.code: permission for permission in session.scalars(select(Permission)).all()}
        roles: dict[str, Role] = {}
        for code, (title, role_permissions) in ROLES.items():
            role = session.scalar(select(Role).where(Role.code == code))
            if role is None:
                role = Role(code=code, title=title, is_system=True)
                session.add(role)
            role.permissions = [permissions[permission] for permission in role_permissions]
            roles[code] = role
        session.flush()
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
