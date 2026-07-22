import uuid

import pytest
from sqlalchemy import select

from app.core.enums import ServiceDeskTicketStatus
from app.modules.notifications.domain import NotificationEventType
from app.modules.notifications.models import ServiceDeskNotification
from app.modules.notifications.service import NotificationDispatcher, ticket_notification
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from test_lifecycle import create_submitted_ticket
from test_tickets import create_requester, create_service_with_template


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


def test_submit_rolls_back_ticket_history_and_notifications_when_dispatch_fails(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requester_id = create_requester(client, db_session_factory)
    service_id, _ = create_service_with_template(client)
    headers = auth_headers_for_user(requester_id)
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "title": "Atomic submission",
            "description": "The submission must roll back as one unit.",
            "field_values": {"room": "305"},
        },
        headers=headers,
    )
    assert draft.status_code == 201, draft.text
    ticket_id = uuid.UUID(draft.json()["id"])

    def fail_dispatch(*_args, **_kwargs) -> None:
        raise RuntimeError("simulated notification failure")

    monkeypatch.setattr(NotificationDispatcher, "dispatch", fail_dispatch)

    with pytest.raises(RuntimeError, match="simulated notification failure"):
        client.post(f"/tickets/{ticket_id}/submit", headers=headers)

    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, ticket_id)
        assert ticket is not None
        assert ticket.status == ServiceDeskTicketStatus.DRAFT
        assert ticket.number is None
        history = db.scalars(
            select(ServiceDeskTicketHistory).where(
                ServiceDeskTicketHistory.ticket_id == ticket_id
            )
        ).all()
        assert [item.event_type for item in history] == ["ticket_created"]
        assert db.scalars(
            select(ServiceDeskNotification).where(
                ServiceDeskNotification.ticket_id == ticket_id
            )
        ).all() == []
