from __future__ import annotations

from platform_sdk.auth import CurrentPrincipal

from app.core.enums import UserRole
from app.modules.users.models import User

PROJECTS_MANAGE_ALL = "projects.manage_all"
PROJECTS_MANAGE_OWN = "projects.manage_own"
PROJECTS_MANAGE_MEMBERS = "projects.manage_members"
PROJECTS_MANAGE_RESPONSES = "projects.manage_responses"
PROJECTS_MANAGE_TASKS = "projects.manage_tasks"
PROJECTS_MANAGE_REPORTS = "projects.manage_reports"
PROJECTS_MANAGE_PERIODS = "projects.manage_periods"
PROJECTS_MANAGE_USERS = "projects.manage_users"
PROJECTS_AUDIT_VIEW = "projects.audit.view"
PLATFORM_ADMIN = "platform.admin"

_LEGACY_ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.EMPLOYEE: frozenset(
        {
            "projects.access",
            "projects.view",
            "projects.respond",
        }
    ),
    UserRole.PROJECT_MANAGER: frozenset(
        {
            "projects.access",
            "projects.view",
            "projects.respond",
            "projects.create",
            PROJECTS_MANAGE_OWN,
            PROJECTS_MANAGE_MEMBERS,
            PROJECTS_MANAGE_TASKS,
            PROJECTS_MANAGE_REPORTS,
        }
    ),
    UserRole.PLATFORM_ADMIN: frozenset({PLATFORM_ADMIN, PROJECTS_MANAGE_ALL}),
}


def bind_principal(user: User, principal: CurrentPrincipal) -> User:
    """Attach request-scoped authorization context to a local profile projection."""

    setattr(user, "_platform_principal", principal)
    return user


def principal_for(user: User) -> CurrentPrincipal | None:
    principal = getattr(user, "_platform_principal", None)
    return principal if isinstance(principal, CurrentPrincipal) else None


def permissions_for(user: User) -> frozenset[str]:
    principal = principal_for(user)
    if principal is not None:
        return principal.permissions
    return _LEGACY_ROLE_PERMISSIONS[user.role]


def has_permission(user: User, permission: str) -> bool:
    permissions = permissions_for(user)
    return permission in permissions or PLATFORM_ADMIN in permissions


def has_any_permission(user: User, *permissions: str) -> bool:
    return any(has_permission(user, permission) for permission in permissions)


def is_platform_admin(user: User) -> bool:
    return has_any_permission(user, PLATFORM_ADMIN, PROJECTS_MANAGE_ALL)


def can_manage_all_projects(user: User) -> bool:
    return has_permission(user, PROJECTS_MANAGE_ALL)


def can_manage_own_projects(user: User) -> bool:
    return has_any_permission(user, PROJECTS_MANAGE_OWN, PROJECTS_MANAGE_ALL)


def compatibility_role(principal: CurrentPrincipal) -> UserRole:
    """Project central permissions into the legacy response field during migration."""

    if principal.has_permission(PROJECTS_MANAGE_ALL):
        return UserRole.PLATFORM_ADMIN
    if principal.has_permission(PROJECTS_MANAGE_OWN):
        return UserRole.PROJECT_MANAGER
    return UserRole.EMPLOYEE
