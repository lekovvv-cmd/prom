import uuid
import os
import socket
from datetime import UTC, datetime, timedelta

from platform_sdk.outbox import (
    cleanup_outbox_records,
    mark_outbox_failed,
    mark_outbox_processed,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.notifications.domain import NotificationEvent, NotificationEventType
from app.modules.notifications.models import ServiceDeskNotificationOutbox
from app.modules.notifications.repository import (
    NotificationOutboxRepository,
    NotificationRepository,
)
from app.modules.notifications.service import InAppChannel


class NotificationOutboxWorker:
    def __init__(self, db: Session, *, worker_id: str | None = None) -> None:
        self.db = db
        self.repository = NotificationOutboxRepository(db)
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}"

    def run_once(self, *, now: datetime | None = None) -> dict[str, int]:
        occurred_at = now or datetime.now(UTC)
        batch_size = settings.notification_outbox_batch_size
        if batch_size < 1:
            raise ValueError("notification_outbox_batch_size must be positive")
        records = self.repository.claim_ready(
            occurred_at,
            worker_id=self.worker_id,
            limit=batch_size,
        )
        result = {"processed": len(records), "sent": 0, "failed": 0, "dead": 0}
        for record in records:
            try:
                if record.channel != "in_app":
                    raise RuntimeError(f"Unsupported notification channel: {record.channel}")
                payload = record.payload
                event = NotificationEvent(
                    event_id=record.event_id,
                    event_type=NotificationEventType(payload["event_type"]),
                    ticket_id=uuid.UUID(payload["ticket_id"]) if payload.get("ticket_id") else None,
                    title=payload["title"],
                    body=payload["body"],
                )
                InAppChannel(NotificationRepository(self.db)).deliver(
                    event, self._recipient_uuid(record.recipient)
                )
                mark_outbox_processed(record, now=occurred_at)
                result["sent"] += 1
            except Exception as exc:  # delivery errors are persisted for retry
                mark_outbox_failed(
                    record,
                    exc,
                    max_attempts=settings.notification_outbox_max_attempts,
                    base_delay_seconds=settings.notification_outbox_retry_base_seconds,
                    max_delay_seconds=settings.notification_outbox_retry_max_seconds,
                    now=occurred_at,
                )
                result["failed"] += 1
                if record.status == "dead":
                    result["dead"] += 1
        deleted = cleanup_outbox_records(
            self.db,
            ServiceDeskNotificationOutbox,
            processed_before=occurred_at
            - timedelta(days=settings.notification_outbox_processed_retention_days),
            dead_before=occurred_at
            - timedelta(days=settings.notification_outbox_dead_retention_days),
            batch_size=settings.notification_outbox_cleanup_batch_size,
        )
        result["cleaned"] = deleted["processed"] + deleted["dead"]
        self.db.commit()
        return result

    @staticmethod
    def _recipient_uuid(value: str):
        return uuid.UUID(value)
