from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from access_service.domain.models import AccessAuditEvent, PlatformUser, Role, UserRoleAssignment
from access_service.infrastructure.identity import ExternalPrincipal


def find_user_by_email(session: Session, email: str) -> PlatformUser | None:
    return session.scalar(
        select(PlatformUser).where(PlatformUser.email == email.lower()).options(selectinload(PlatformUser.assignments).selectinload(UserRoleAssignment.role).selectinload(Role.permissions))
    )


def require_user(session: Session, user_id: str) -> PlatformUser:
    user = session.scalar(
        select(PlatformUser).where(PlatformUser.id == user_id).options(selectinload(PlatformUser.assignments).selectinload(UserRoleAssignment.role).selectinload(Role.permissions))
    )
    if user is None or not user.is_active:
        raise LookupError("Platform user was not found or is inactive")
    return user


def permissions_for(user: PlatformUser) -> set[str]:
    permissions: set[str] = set()
    for assignment in user.assignments:
        for permission in assignment.role.permissions:
            permissions.add(permission.code)
    return permissions


def modules_for_permissions(permissions: set[str]) -> list[dict[str, object]]:
    modules: list[dict[str, object]] = []
    for module_id in ("projects", "service-desk"):
        module_permissions = sorted(permission for permission in permissions if permission.startswith(module_id.replace("-", "_") + "."))
        if module_permissions:
            modules.append({"id": module_id, "permissions": module_permissions})
    return modules


def record_audit(
    session: Session,
    *,
    actor_user_id: str | None,
    action: str,
    object_type: str,
    object_id: str,
    before: dict[str, object] | None = None,
    after: dict[str, object] | None = None,
    request_id: str | None = None,
) -> None:
    session.add(
        AccessAuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            before=before,
            after=after,
            request_id=request_id,
        )
    )


def mark_login(session: Session, user: PlatformUser) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    session.flush()


def sync_external_principal(
    session: Session,
    principal: ExternalPrincipal,
) -> PlatformUser:
    user = session.scalar(
        select(PlatformUser)
        .where(PlatformUser.external_subject == principal.subject)
        .options(
            selectinload(PlatformUser.assignments)
            .selectinload(UserRoleAssignment.role)
            .selectinload(Role.permissions)
        )
    )
    if user is None:
        user = find_user_by_email(session, principal.email)
    if user is None:
        user = PlatformUser(
            external_subject=principal.subject,
            email=principal.email.lower(),
            display_name=principal.display_name,
            department=principal.department,
        )
        session.add(user)
        session.flush()
    else:
        user.external_subject = principal.subject
        user.email = principal.email.lower()
        user.display_name = principal.display_name
        user.department = principal.department
    mark_login(session, user)
    return user


def revoke_sessions(session: Session, user: PlatformUser) -> None:
    user.session_version += 1
    session.flush()
