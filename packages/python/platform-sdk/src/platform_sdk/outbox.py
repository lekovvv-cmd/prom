from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from sqlalchemy import JSON, DateTime, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, declarative_mixin, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


@declarative_mixin
class OutboxEventMixin:
    event_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )


@declarative_mixin
class AuditEventMixin:
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    external_user_id: Mapped[str | None] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    object_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(String(500))
    request_id: Mapped[str | None] = mapped_column(String(128), index=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="api")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )


@declarative_mixin
class IdempotencyRecordMixin:
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scope: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: utc_now() + timedelta(days=1),
        index=True,
    )


OutboxT = TypeVar("OutboxT", bound=OutboxEventMixin)


def claim_outbox_batch(
    session: Session,
    model: type[OutboxT],
    *,
    worker_id: str,
    batch_size: int,
    now: datetime | None = None,
) -> list[OutboxT]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    claimed_at = now or utc_now()
    statement = (
        select(model)
        .where(
            model.status.in_(("pending", "retry")),
            model.next_attempt_at <= claimed_at,
        )
        .order_by(model.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    records = list(session.scalars(statement).all())
    for record in records:
        record.status = "processing"
        record.locked_at = claimed_at
        record.locked_by = worker_id
    session.flush()
    return records


def mark_outbox_processed(record: OutboxEventMixin, *, now: datetime | None = None) -> None:
    record.status = "processed"
    record.processed_at = now or utc_now()
    record.locked_at = None
    record.locked_by = None
    record.last_error = None


def mark_outbox_failed(
    record: OutboxEventMixin,
    error: BaseException | str,
    *,
    max_attempts: int = 8,
    base_delay_seconds: int = 5,
    max_delay_seconds: int = 3600,
    now: datetime | None = None,
) -> None:
    failed_at = now or utc_now()
    record.attempts += 1
    record.last_error = str(error)[:4000]
    record.locked_at = None
    record.locked_by = None
    if record.attempts >= max_attempts:
        record.status = "dead"
        record.next_attempt_at = failed_at
        return
    delay = min(base_delay_seconds * (2 ** max(record.attempts - 1, 0)), max_delay_seconds)
    record.status = "retry"
    record.next_attempt_at = failed_at + timedelta(seconds=delay)


def outbox_metrics(session: Session, model: type[OutboxT]) -> dict[str, int | float | None]:
    now = utc_now()
    pending = session.scalar(
        select(func.count()).select_from(model).where(model.status.in_(("pending", "retry")))
    )
    oldest = session.scalar(
        select(func.min(model.created_at)).where(model.status.in_(("pending", "retry")))
    )
    oldest_age = None
    if isinstance(oldest, datetime):
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=UTC)
        oldest_age = max((now - oldest).total_seconds(), 0.0)
    return {
        "pending": int(pending or 0),
        "oldest_age_seconds": oldest_age,
    }


def cleanup_outbox_records(
    session: Session,
    model: type[OutboxT],
    *,
    processed_before: datetime,
    dead_before: datetime,
    batch_size: int = 500,
) -> dict[str, int]:
    """Delete terminal outbox rows in a bounded, concurrency-safe batch."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    statement = (
        select(model)
        .where(
            (
                (model.status == "processed")
                & (model.processed_at.is_not(None))
                & (model.processed_at < processed_before)
            )
            | ((model.status == "dead") & (model.next_attempt_at < dead_before))
        )
        .order_by(model.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    records = list(session.scalars(statement).all())
    deleted = {"processed": 0, "dead": 0}
    for record in records:
        if record.status == "processed":
            deleted["processed"] += 1
        elif record.status == "dead":
            deleted["dead"] += 1
        session.delete(record)
    session.flush()
    return deleted
