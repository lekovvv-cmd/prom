from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability

DEMO_PROFILE_RULES: dict[str, dict[str, Any] | None] = {
    "employee@utmn.ru": None,
    "project.manager@utmn.ru": None,
    "admin@utmn.ru": None,
    "sd.manager@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_MANAGER,
        "capabilities": (
            "service_desk.be_assignee",
            "service_desk.approve",
            "service_desk.assign",
            "service_desk.change_priority",
        ),
    },
    "sd.admin@utmn.ru": {
        "access_type": ServiceDeskAccessType.SERVICE_DESK_ADMIN,
        "capabilities": (),
    },
}


@dataclass(frozen=True)
class IdentityBootstrapResult:
    created: int
    updated: int
    skipped: int


def repair_service_desk_users(
    db: Session,
    platform_users: Iterable[dict[str, Any]],
) -> IdentityBootstrapResult:
    created = updated = skipped = 0
    for platform_user in platform_users:
        email = str(platform_user.get("email") or "").strip().lower()
        rule = DEMO_PROFILE_RULES.get(email)
        identity_user_id = str(platform_user.get("id") or "").strip()
        if email not in DEMO_PROFILE_RULES or not email or not identity_user_id:
            skipped += 1
            continue

        rule = DEMO_PROFILE_RULES[email]
        user = db.scalar(
            select(ServiceDeskUser).where(ServiceDeskUser.identity_user_id == identity_user_id)
        )
        if user is None:
            user = db.scalar(
                select(ServiceDeskUser).where(ServiceDeskUser.email == email)
            )
        if rule is None:
            if user is None:
                skipped += 1
                continue
            user.identity_user_id = identity_user_id
            user.email = email
            user.display_name = str(platform_user.get("full_name") or email)
            user.is_active = False
            user.capabilities.clear()
            updated += 1
            continue
        if user is None:
            user = ServiceDeskUser(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"prom:service-desk:{identity_user_id}"),
                identity_user_id=identity_user_id,
                email=email,
                display_name=str(platform_user.get("full_name") or email),
                department=platform_user.get("department"),
                position=platform_user.get("position"),
                access_type=rule["access_type"],
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1
        else:
            user.identity_user_id = identity_user_id
            user.email = email
            user.display_name = str(platform_user.get("full_name") or email)
            user.department = platform_user.get("department")
            user.position = platform_user.get("position")
            user.access_type = rule["access_type"]
            user.is_active = True
            updated += 1

        user.capabilities.clear()
        if user.access_type != ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            user.capabilities.extend(
                ServiceDeskUserCapability(capability=capability)
                for capability in rule["capabilities"]
            )

    return IdentityBootstrapResult(created=created, updated=updated, skipped=skipped)
