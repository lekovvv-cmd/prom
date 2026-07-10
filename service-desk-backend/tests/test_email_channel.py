import uuid

from sqlalchemy import select

from app.modules.notifications.models import ServiceDeskNotification, ServiceDeskNotificationOutbox
from app.modules.notifications.worker import NotificationOutboxWorker
from test_lifecycle import create_submitted_ticket


def test_email_required_event_is_blocked_external_while_in_app_is_delivered(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, requester_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    with db_session_factory() as db:
        email_record = db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.channel == "email",
            ServiceDeskNotificationOutbox.payload["ticket_id"].as_string() == ticket_id,
            ServiceDeskNotificationOutbox.payload["event_type"].as_string() == "ticket_submitted",
        ))
        assert email_record is not None
        assert email_record.status == "blocked_external"
        assert email_record.processed_at is None
        assert db.scalar(select(ServiceDeskNotification.id).where(
            ServiceDeskNotification.event_id == email_record.event_id,
            ServiceDeskNotification.recipient_user_id == uuid.UUID(requester_id),
        )) is not None
        event_id = email_record.event_id

    with db_session_factory() as db:
        result = NotificationOutboxWorker(db).run_once()
        assert result["sent"] == 0
        email_record = db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.event_id == event_id,
            ServiceDeskNotificationOutbox.channel == "email",
        ))
        assert email_record.status == "blocked_external"
        assert email_record.retry_count == 0
        assert email_record.processed_at is None
