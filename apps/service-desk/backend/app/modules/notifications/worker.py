import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.notifications.domain import NotificationEvent, NotificationEventType
from app.modules.notifications.repository import NotificationOutboxRepository, NotificationRepository
from app.modules.notifications.service import InAppChannel


class NotificationOutboxWorker:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = NotificationOutboxRepository(db)

    def run_once(self, *, now: datetime | None = None) -> dict[str, int]:
        occurred_at = now or datetime.now(UTC)
        batch_size = settings.notification_outbox_batch_size
        if batch_size < 1:
            raise ValueError("notification_outbox_batch_size must be positive")
        records = self.repository.ready_for_processing(occurred_at, limit=batch_size)
        result = {"processed": len(records), "sent": 0, "failed": 0}
        for record in records:
            record.status = "processing"
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
                record.status = "sent"
                record.processed_at = occurred_at
                record.last_error = None
                result["sent"] += 1
            except Exception as exc:  # delivery errors are persisted for retry
                record.status = "failed"
                record.retry_count += 1
                record.next_retry_at = occurred_at + timedelta(minutes=min(60, 2 ** record.retry_count))
                record.last_error = str(exc)[:1000]
                result["failed"] += 1
        self.db.commit()
        return result

    @staticmethod
    def _recipient_uuid(value: str):
        return uuid.UUID(value)
