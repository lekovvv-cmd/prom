import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select

from app.core.config import settings
from app.modules.notifications.models import ServiceDeskNotification, ServiceDeskNotificationOutbox
from app.modules.notifications.worker import NotificationOutboxWorker
from test_lifecycle import create_submitted_ticket


def test_business_event_persists_sent_in_app_outbox_atomically(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, requester_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    with db_session_factory() as db:
        record = db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.channel == "in_app",
            ServiceDeskNotificationOutbox.recipient == requester_id,
            ServiceDeskNotificationOutbox.payload["ticket_id"].as_string() == ticket_id,
            ServiceDeskNotificationOutbox.payload["event_type"].as_string() == "ticket_submitted",
        ))
        assert record is not None
        assert record.status == "processed"
        assert record.processed_at is not None
        assert record.event_type == "ticket_submitted"
        assert record.aggregate_type == "service_desk_ticket"
        assert record.aggregate_id == ticket_id
        assert record.payload_version == 1
        assert db.scalar(select(ServiceDeskNotification.id).where(
            ServiceDeskNotification.event_id == record.event_id,
            ServiceDeskNotification.recipient_user_id == uuid.UUID(requester_id),
        )) is not None


def test_outbox_worker_retries_idempotently_without_duplicate_notification(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, _ = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    with db_session_factory() as db:
        record = db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.channel == "in_app",
            ServiceDeskNotificationOutbox.payload["ticket_id"].as_string() == ticket_id,
            ServiceDeskNotificationOutbox.payload["event_type"].as_string() == "ticket_submitted",
        ))
        db.execute(delete(ServiceDeskNotification).where(ServiceDeskNotification.event_id == record.event_id))
        record.status = "pending"
        record.processed_at = None
        event_id = record.event_id
        db.commit()

    with db_session_factory() as db:
        assert NotificationOutboxWorker(db).run_once()["sent"] == 1
        assert NotificationOutboxWorker(db).run_once()["processed"] == 0
        count = db.scalar(select(func.count()).select_from(ServiceDeskNotification).where(
            ServiceDeskNotification.event_id == event_id
        ))
        assert count == 1


def test_outbox_worker_retries_then_dead_letters_invalid_payload(
    client, db_session_factory, auth_headers_for_user, monkeypatch
):
    ticket_id, _ = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    monkeypatch.setattr(settings, "notification_outbox_max_attempts", 2)
    monkeypatch.setattr(settings, "notification_outbox_retry_base_seconds", 1)
    with db_session_factory() as db:
        record = db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.channel == "in_app",
            ServiceDeskNotificationOutbox.aggregate_id == ticket_id,
        ))
        assert record is not None
        record_id = record.id
        record.payload = {"event_type": "ticket_submitted"}
        record.status = "pending"
        record.processed_at = None
        db.commit()

    first_attempt = datetime.now(UTC)
    with db_session_factory() as db:
        result = NotificationOutboxWorker(db, worker_id="test-worker").run_once(
            now=first_attempt
        )
        record = db.get(ServiceDeskNotificationOutbox, record_id)
        assert record is not None
        assert result["failed"] == 1
        assert result["dead"] == 0
        assert record.status == "retry"
        assert record.attempts == 1
        assert record.locked_at is None
        assert record.locked_by is None
        expected_retry_at = first_attempt + timedelta(seconds=1)
        assert record.next_attempt_at.replace(tzinfo=UTC) == expected_retry_at

    with db_session_factory() as db:
        result = NotificationOutboxWorker(db, worker_id="test-worker").run_once(
            now=first_attempt + timedelta(seconds=1)
        )
        record = db.get(ServiceDeskNotificationOutbox, record_id)
        assert record is not None
        assert result["failed"] == 1
        assert result["dead"] == 1
        assert record.status == "dead"
        assert record.attempts == 2
