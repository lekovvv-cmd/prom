from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import String, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from platform_sdk.outbox import (
    AuditEventMixin,
    IdempotencyRecordMixin,
    OutboxEventMixin,
    claim_outbox_batch,
    cleanup_outbox_records,
    mark_outbox_failed,
    mark_outbox_processed,
    outbox_metrics,
)


class Base(DeclarativeBase):
    pass


class OutboxRecord(OutboxEventMixin, Base):
    __tablename__ = "outbox_records"


class AuditRecord(AuditEventMixin, Base):
    __tablename__ = "audit_records"


class IdempotencyRecord(IdempotencyRecordMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("scope", "idempotency_key", name="uq_test_idempotency"),
    )
    owner: Mapped[str] = mapped_column(String(36), default="test")


def test_outbox_claim_retry_and_process_lifecycle() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        record = OutboxRecord(
            event_type="ProjectCreated",
            aggregate_type="project",
            aggregate_id="project-1",
            payload={"version": 1},
        )
        session.add(record)
        session.commit()

        claimed = claim_outbox_batch(
            session,
            OutboxRecord,
            worker_id="worker-1",
            batch_size=10,
            now=datetime.now(UTC),
        )
        assert claimed == [record]
        assert record.status == "processing"

        mark_outbox_failed(record, "temporary", base_delay_seconds=1)
        assert record.status == "retry"
        assert record.attempts == 1

        record.next_attempt_at = datetime.now(UTC)
        claimed = claim_outbox_batch(
            session,
            OutboxRecord,
            worker_id="worker-2",
            batch_size=10,
            now=datetime.now(UTC),
        )
        mark_outbox_processed(claimed[0])
        session.commit()

        assert outbox_metrics(session, OutboxRecord) == {
            "pending": 0,
            "oldest_age_seconds": None,
        }


def test_outbox_cleanup_is_bounded_and_respects_terminal_retention() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.add_all(
            [
                OutboxRecord(
                    event_type="Delivered",
                    aggregate_type="project",
                    aggregate_id="old-processed",
                    payload={},
                    status="processed",
                    processed_at=now - timedelta(days=31),
                    created_at=now - timedelta(days=31),
                ),
                OutboxRecord(
                    event_type="Failed",
                    aggregate_type="project",
                    aggregate_id="old-dead",
                    payload={},
                    status="dead",
                    next_attempt_at=now - timedelta(days=91),
                    created_at=now - timedelta(days=91),
                ),
                OutboxRecord(
                    event_type="Delivered",
                    aggregate_type="project",
                    aggregate_id="recent",
                    payload={},
                    status="processed",
                    processed_at=now - timedelta(days=1),
                    created_at=now - timedelta(days=1),
                ),
            ]
        )
        session.commit()

        deleted = cleanup_outbox_records(
            session,
            OutboxRecord,
            processed_before=now - timedelta(days=30),
            dead_before=now - timedelta(days=90),
            batch_size=2,
        )
        session.commit()

        assert deleted == {"processed": 1, "dead": 1}
        assert session.scalar(
            select(func.count()).select_from(OutboxRecord)
        ) == 1
