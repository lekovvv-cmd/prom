import uuid

from sqlalchemy import select

from app.modules.access.models import ServiceDeskAccessAuditEvent


def test_admin_can_manage_local_access_with_audit(client, db_session_factory):
    identity = str(uuid.uuid4())
    response = client.post(
        "/admin/access/users",
        json={
            "identity_user_id": identity,
            "email": "manager@utmn.ru",
            "display_name": "Manager",
            "access_type": "manager",
            "capabilities": ["service_desk.access", "service_desk.view_reports"],
        },
    )
    assert response.status_code == 201
    user = response.json()
    assert user["capabilities"] == ["service_desk.access", "service_desk.view_reports"]
    replaced = client.put(
        f"/admin/access/users/{user['id']}/capabilities",
        json={"capabilities": ["service_desk.access", "service_desk.access"]},
    )
    assert replaced.status_code == 200 and replaced.json()["capabilities"] == [
        "service_desk.access"
    ]
    assert (
        client.put(
            f"/admin/access/users/{user['id']}/capabilities", json={"capabilities": ["unknown"]}
        ).status_code
        == 422
    )
    assert client.post(f"/admin/access/users/{user['id']}/deactivate").json()["is_active"] is False
    assert client.post(f"/admin/access/users/{user['id']}/activate").json()["is_active"] is True
    with db_session_factory() as db:
        events = db.scalars(
            select(ServiceDeskAccessAuditEvent)
            .where(ServiceDeskAccessAuditEvent.target_user_id == uuid.UUID(user["id"]))
            .order_by(ServiceDeskAccessAuditEvent.created_at)
        ).all()
        assert [event.event_type for event in events] == [
            "access_user_created",
            "capabilities_replaced",
            "access_deactivated",
            "access_activated",
        ]
        assert events[0].actor_user_id != events[0].target_user_id


def test_admin_to_manager_requires_explicit_manager_capabilities(client):
    created = client.post(
        "/admin/access/users",
        json={
            "identity_user_id": str(uuid.uuid4()),
            "email": "admin2@utmn.ru",
            "display_name": "Admin 2",
            "access_type": "service_desk_admin",
        },
    ).json()
    updated = client.patch(f"/admin/access/users/{created['id']}", json={"access_type": "manager"})
    assert updated.status_code == 200 and updated.json()["capabilities"] == []
