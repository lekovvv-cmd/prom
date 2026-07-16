import uuid

from app.modules.notifications.models import ServiceDeskNotification
from test_lifecycle import create_submitted_ticket, create_user


def test_notification_api_is_current_user_scoped_and_read_is_idempotent(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, requester_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    foreign_id = create_user(db_session_factory, "notification-foreign@utmn.ru")
    with db_session_factory() as db:
        foreign = ServiceDeskNotification(
            event_id=uuid.uuid4(), recipient_user_id=uuid.UUID(foreign_id),
            ticket_id=uuid.UUID(ticket_id), event_type="ticket_started",
            title="Foreign", body="Foreign notification",
        )
        db.add(foreign)
        db.commit()
        db.refresh(foreign)
        foreign_notification_id = str(foreign.id)

    headers = auth_headers_for_user(requester_id)
    notifications = client.get(
        f"/notifications?recipient_user_id={foreign_id}", headers=headers
    )
    assert notifications.status_code == 200
    assert notifications.json()
    assert {item["recipient_user_id"] for item in notifications.json()} == {requester_id}
    own_id = notifications.json()[0]["id"]

    assert client.get("/notifications").status_code == 401
    assert client.post(f"/notifications/{foreign_notification_id}/read", headers=headers).status_code == 404
    assert client.post(f"/notifications/{own_id}/read", json={"recipient_user_id": foreign_id}, headers=headers).status_code == 200
    first_read_at = client.post(f"/notifications/{own_id}/read", headers=headers).json()["read_at"]
    second = client.post(f"/notifications/{own_id}/read", headers=headers)
    assert second.status_code == 200
    assert second.json()["read_at"] == first_read_at
    assert all(item["id"] != own_id for item in client.get(
        "/notifications?unread_only=true", headers=headers
    ).json())


def test_read_all_only_marks_current_users_notifications(
    client, db_session_factory, auth_headers_for_user
):
    _, requester_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    foreign_id = create_user(db_session_factory, "read-all-foreign@utmn.ru")
    with db_session_factory() as db:
        foreign = ServiceDeskNotification(
            event_id=uuid.uuid4(), recipient_user_id=uuid.UUID(foreign_id),
            event_type="sla_warning", title="Foreign", body="Foreign",
        )
        db.add(foreign)
        db.commit()
        foreign_notification_id = foreign.id

    result = client.post("/notifications/read-all", headers=auth_headers_for_user(requester_id))
    assert result.status_code == 200
    assert result.json()["marked_read"] >= 1
    with db_session_factory() as db:
        assert db.get(ServiceDeskNotification, foreign_notification_id).is_read is False
