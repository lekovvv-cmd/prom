from __future__ import annotations

from typing import Any

from platform_sdk.observability import get_request_id
from sqlalchemy.orm import Session

from app.core.permissions import principal_for
from app.modules.platform.models import ProjectAuditEvent, ProjectOutboxEvent
from app.modules.users.models import User


class ProjectEventRecorder:
    """Append-only audit and integration events in the caller's transaction."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def audit(
        self,
        *,
        actor: User | None,
        action: str,
        object_type: str,
        object_id: object,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        reason: str | None = None,
        result: str = "success",
        source: str = "api",
    ) -> ProjectAuditEvent:
        principal = principal_for(actor) if actor is not None else None
        event = ProjectAuditEvent(
            actor_user_id=str(actor.id) if actor is not None else None,
            external_user_id=principal.external_subject if principal is not None else None,
            action=action,
            module="projects",
            object_type=object_type,
            object_id=str(object_id),
            before=before,
            after=after,
            reason=reason,
            request_id=get_request_id(),
            result=result,
            source=source,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def publish(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: object,
        payload: dict[str, Any],
        payload_version: int = 1,
    ) -> ProjectOutboxEvent:
        event = ProjectOutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=payload,
            payload_version=payload_version,
        )
        self.db.add(event)
        self.db.flush()
        return event


def project_snapshot(project: object) -> dict[str, Any]:
    return {
        "title": getattr(project, "title", None),
        "status": getattr(getattr(project, "status", None), "value", None),
        "responsible_user_id": (
            str(value)
            if (value := getattr(project, "responsible_user_id", None)) is not None
            else None
        ),
        "version": getattr(project, "version", None),
    }
