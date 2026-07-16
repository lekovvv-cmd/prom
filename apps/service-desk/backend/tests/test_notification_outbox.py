import uuid

from sqlalchemy import delete, func, select

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
        assert record.status == "sent"
        assert record.processed_at is not None
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
