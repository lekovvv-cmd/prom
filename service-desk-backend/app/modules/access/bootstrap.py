from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


DEMO_PROFILE_RULES: dict[str, dict[str, Any]] = {
    "admin@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_ADMIN,
        "capabilities": (),
    },
    "manager@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_MANAGER,
        "capabilities": (
            "service_desk.approve",
            "service_desk.assign",
            "service_desk.view_reports",
            "service_desk.manage_catalog",
            "service_desk.manage_templates",
            "service_desk.manage_approval_workflows",
            "service_desk.manage_sla",
        ),
    },
    "employee@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_MANAGER,
        "capabilities": ("service_desk.be_assignee",),
    },
    "analyst@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_MANAGER,
        "capabilities": (
            "service_desk.be_assignee",
        ),
    },
}


@dataclass(frozen=True)
class IdentityBootstrapResult:
    created: int
    updated: int
    skipped: int


def repair_service_desk_users(
    db: Session,
    project_users: Iterable[dict[str, Any]],
) -> IdentityBootstrapResult:
    created = updated = skipped = 0
    for project_user in project_users:
        email = str(project_user.get("email") or "").strip().lower()
        rule = DEMO_PROFILE_RULES.get(email)
        identity_user_id = str(project_user.get("id") or "").strip()
        if not rule or not email or not identity_user_id:
            skipped += 1
            continue

        user = db.scalar(select(ServiceDeskUser).where(ServiceDeskUser.email == email))
        if user is None:
            user = db.scalar(
                select(ServiceDeskUser).where(
                    ServiceDeskUser.identity_user_id == identity_user_id
                )
            )
        if user is None:
            user = ServiceDeskUser(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"prom:service-desk:{identity_user_id}"),
                identity_user_id=identity_user_id,
                email=email,
                display_name=str(project_user.get("full_name") or email),
                department=project_user.get("department"),
                position=project_user.get("position"),
                access_type=rule["access_type"],
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1
        else:
            user.identity_user_id = identity_user_id
            user.email = email
            user.display_name = str(project_user.get("full_name") or email)
            user.department = project_user.get("department")
            user.position = project_user.get("position")
            user.access_type = rule["access_type"]
            user.is_active = True
            updated += 1

        if user.access_type != ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            existing = {item.capability for item in user.capabilities}
            for capability in rule["capabilities"]:
                if capability not in existing:
                    db.add(ServiceDeskUserCapability(service_desk_user_id=user.id, capability=capability))

    return IdentityBootstrapResult(created=created, updated=updated, skipped=skipped)
