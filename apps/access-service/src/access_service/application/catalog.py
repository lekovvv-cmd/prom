from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from access_service.domain.models import Module, Permission, Role


MODULES = {
    "projects": "Projects",
    "service-desk": "Service Desk",
}

PERMISSIONS = {
    "platform.admin": "Platform administration",
    "projects.access": "Access Projects",
    "projects.view": "View Projects",
    "projects.respond": "Respond to projects",
    "projects.manage_own": "Manage own projects",
    "projects.manage_all": "Manage all projects",
    "projects.create": "Create projects",
    "projects.update_own": "Update own projects",
    "projects.update_any": "Update any project",
    "projects.manage_members": "Manage project members",
    "projects.manage_responses": "Manage project responses",
    "projects.manage_tasks": "Manage project tasks",
    "projects.manage_reports": "Manage project reports",
    "projects.manage_periods": "Manage project report periods",
    "projects.manage_users": "Manage project users",
    "projects.manage_settings": "Manage project settings",
    "projects.audit.view": "View project audit log",
    "service_desk.access": "Access Service Desk",
    "service_desk.be_assignee": "Be assigned to Service Desk tickets",
    "service_desk.assign": "Assign Service Desk tickets",
    "service_desk.approve": "Approve Service Desk tickets",
    "service_desk.change_priority": "Change Service Desk ticket priority",
    "service_desk.view_all_tickets": "View all Service Desk tickets",
    "service_desk.view_reports": "View Service Desk reports",
    "service_desk.manage_catalog": "Manage Service Desk catalog",
    "service_desk.manage_sla": "Manage Service Desk SLA",
    "service_desk.manage_access": "Manage Service Desk access",
    "service_desk.manage_templates": "Manage Service Desk templates",
    "service_desk.manage_routing": "Manage Service Desk routing",
    "service_desk.manage_approval_workflows": "Manage approval workflows",
}

ROLES: dict[str, tuple[str, str | None, set[str]]] = {
    "employee": (
        "Сотрудник",
        "projects",
        {"projects.access", "projects.view", "projects.respond"},
    ),
    "project_manager": (
        "Руководитель проектов",
        "projects",
        {
            "projects.access",
            "projects.view",
            "projects.respond",
            "projects.create",
            "projects.update_own",
            "projects.manage_own",
            "projects.manage_members",
            "projects.manage_responses",
            "projects.manage_tasks",
            "projects.manage_reports",
        },
    ),
    "service_desk_manager": (
        "Менеджер Service Desk",
        "service-desk",
        {
            "service_desk.access",
            "service_desk.be_assignee",
            "service_desk.assign",
            "service_desk.approve",
            "service_desk.change_priority",
            "service_desk.view_all_tickets",
            "service_desk.view_reports",
        },
    ),
    "service_desk_admin": (
        "Администратор Service Desk",
        "service-desk",
        {
            "service_desk.access",
            "service_desk.be_assignee",
            "service_desk.assign",
            "service_desk.approve",
            "service_desk.change_priority",
            "service_desk.view_all_tickets",
            "service_desk.view_reports",
            "service_desk.manage_catalog",
            "service_desk.manage_sla",
            "service_desk.manage_access",
            "service_desk.manage_templates",
            "service_desk.manage_routing",
            "service_desk.manage_approval_workflows",
        },
    ),
}
ROLES["platform_admin"] = (
    "Администратор платформы",
    None,
    set(PERMISSIONS),
)


def permission_module(code: str) -> str | None:
    if code.startswith("projects."):
        return "projects"
    if code.startswith("service_desk."):
        return "service-desk"
    return None


def ensure_access_catalog(session: Session) -> dict[str, Role]:
    """Create or reconcile the platform RBAC catalog without creating demo users."""

    for module_id, title in MODULES.items():
        module = session.get(Module, module_id)
        if module is None:
            session.add(Module(id=module_id, title=title, is_active=True))
        else:
            module.title = title
    session.flush()

    for code, title in PERMISSIONS.items():
        permission = session.scalar(select(Permission).where(Permission.code == code))
        permission_module_id = permission_module(code)
        if permission is None:
            session.add(
                Permission(code=code, title=title, module_id=permission_module_id)
            )
        else:
            permission.title = title
            permission.module_id = permission_module_id
    session.flush()

    permissions = {
        permission.code: permission for permission in session.scalars(select(Permission)).all()
    }
    roles: dict[str, Role] = {}
    for code, (title, role_module_id, permission_codes) in ROLES.items():
        role = session.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(
                code=code,
                title=title,
                module_id=role_module_id,
                is_system=True,
            )
            session.add(role)
        else:
            role.title = title
            role.module_id = role_module_id
            role.is_system = True
        role.permissions = [permissions[permission_code] for permission_code in permission_codes]
        roles[code] = role
    session.flush()
    return roles
