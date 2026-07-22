from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from access_service.domain.models import (
    AccessAuditEvent,
    GroupMembership,
    GroupRoleAssignment,
    Module,
    Permission,
    PlatformUser,
    Role,
    UserRoleAssignment,
    role_permissions,
)
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


def permissions_for(session: Session, user: PlatformUser) -> set[str]:
    direct = select(Permission.code).join(
        role_permissions,
        role_permissions.c.permission_id == Permission.id,
    ).join(
        UserRoleAssignment,
        UserRoleAssignment.role_id == role_permissions.c.role_id,
    ).where(UserRoleAssignment.user_id == user.id)
    through_groups = select(Permission.code).join(
        role_permissions,
        role_permissions.c.permission_id == Permission.id,
    ).join(
        GroupRoleAssignment,
        GroupRoleAssignment.role_id == role_permissions.c.role_id,
    ).join(
        GroupMembership,
        GroupMembership.group_id == GroupRoleAssignment.group_id,
    ).where(GroupMembership.user_id == user.id)
    return set(session.scalars(direct.union(through_groups)).all())


def modules_for_permissions(
    session: Session,
    permissions: set[str],
) -> list[dict[str, object]]:
    if not permissions:
        return []
    rows = session.execute(
        select(Module.id, Permission.code)
        .join(Permission, Permission.module_id == Module.id)
        .where(Module.is_active.is_(True), Permission.code.in_(permissions))
        .order_by(Module.id, Permission.code)
    ).all()
    grouped: dict[str, list[str]] = {}
    for module_id, permission_code in rows:
        grouped.setdefault(module_id, []).append(permission_code)
    return [
        {"id": module_id, "permissions": module_permissions}
        for module_id, module_permissions in grouped.items()
    ]


def user_ids_for_permission(session: Session, permission_code: str) -> set[str]:
    direct = select(UserRoleAssignment.user_id).join(
        role_permissions,
        role_permissions.c.role_id == UserRoleAssignment.role_id,
    ).join(
        Permission,
        Permission.id == role_permissions.c.permission_id,
    ).where(Permission.code == permission_code)
    through_groups = select(GroupMembership.user_id).join(
        GroupRoleAssignment,
        GroupRoleAssignment.group_id == GroupMembership.group_id,
    ).join(
        role_permissions,
        role_permissions.c.role_id == GroupRoleAssignment.role_id,
    ).join(
        Permission,
        Permission.id == role_permissions.c.permission_id,
    ).where(Permission.code == permission_code)
    candidate_ids = set(session.scalars(direct.union(through_groups)).all())
    if not candidate_ids:
        return set()
    return set(
        session.scalars(
            select(PlatformUser.id).where(
                PlatformUser.id.in_(candidate_ids),
                PlatformUser.is_active.is_(True),
            )
        ).all()
    )


def affected_users_for_role(session: Session, role_id: str) -> list[PlatformUser]:
    direct = select(UserRoleAssignment.user_id).where(UserRoleAssignment.role_id == role_id)
    through_groups = select(GroupMembership.user_id).join(
        GroupRoleAssignment,
        GroupRoleAssignment.group_id == GroupMembership.group_id,
    ).where(GroupRoleAssignment.role_id == role_id)
    user_ids = set(session.scalars(direct.union(through_groups)).all())
    if not user_ids:
        return []
    return list(
        session.scalars(select(PlatformUser).where(PlatformUser.id.in_(user_ids))).all()
    )


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
