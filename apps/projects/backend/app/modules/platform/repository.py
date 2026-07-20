from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform.models import ProjectAuditEvent


class ProjectAuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_events(
        self,
        *,
        action: str | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProjectAuditEvent]:
        query = select(ProjectAuditEvent)
        if action:
            query = query.where(ProjectAuditEvent.action == action)
        if object_type:
            query = query.where(ProjectAuditEvent.object_type == object_type)
        if object_id:
            query = query.where(ProjectAuditEvent.object_id == object_id)
        return list(
            self.db.scalars(
                query.order_by(ProjectAuditEvent.created_at.desc())
                .limit(min(max(limit, 1), 200))
                .offset(max(offset, 0))
            )
        )
