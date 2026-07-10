import uuid

from sqlalchemy import select

from app.modules.notifications.domain import NotificationEventType
from app.modules.notifications.models import ServiceDeskNotification
from app.modules.notifications.service import NotificationDispatcher, ticket_notification
from tests.test_lifecycle import create_submitted_ticket


def test_submit_produces_transactional_in_app_notification(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, requester_id = create_submitted_ticket(
        client, db_session_factory, auth_headers_for_user
    )

    with db_session_factory() as db:
        notification = db.scalar(select(ServiceDeskNotification).where(
            ServiceDeskNotification.ticket_id == uuid.UUID(ticket_id),
            ServiceDeskNotification.event_type == "ticket_submitted",
        ))
        assert notification is not None
        assert notification.recipient_user_id == uuid.UUID(requester_id)
        assert notification.is_read is False
        assert notification.read_at is None


def test_in_app_channel_is_idempotent_for_same_event(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, _ = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    event = ticket_notification(NotificationEventType.SLA_WARNING, uuid.UUID(ticket_id))

    with db_session_factory() as db:
        dispatcher = NotificationDispatcher(db)
        dispatcher.dispatch(event)
        dispatcher.dispatch(event)
        db.commit()
        notifications = db.scalars(select(ServiceDeskNotification).where(
            ServiceDeskNotification.event_id == event.event_id
        )).all()
        assert len(notifications) == 1
