from __future__ import annotations

from sqlalchemy import UniqueConstraint
from platform_sdk.outbox import AuditEventMixin, IdempotencyRecordMixin, OutboxEventMixin

from app.core.database import Base


class ProjectOutboxEvent(OutboxEventMixin, Base):
    __tablename__ = "project_outbox_events"


class ProjectAuditEvent(AuditEventMixin, Base):
    __tablename__ = "project_audit_events"


class ProjectIdempotencyRecord(IdempotencyRecordMixin, Base):
    __tablename__ = "project_idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "scope",
            "idempotency_key",
            name="uq_project_idempotency_scope_key",
        ),
    )
