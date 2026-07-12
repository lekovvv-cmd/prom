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
            "access_type": "service_desk_manager",
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
    updated = client.patch(f"/admin/access/users/{created['id']}", json={"access_type": "service_desk_manager"})
    assert updated.status_code == 200 and updated.json()["capabilities"] == []


def test_access_patch_validation_and_capability_mutation_are_isolated(
    client, db_session_factory
):
    created = client.post(
        "/admin/access/users",
        json={
            "identity_user_id": str(uuid.uuid4()),
            "email": "  patch-user@utmn.ru ",
            "display_name": " Patch User ",
            "department": "  IT  ",
            "position": "  Analyst  ",
            "access_type": "service_desk_manager",
            "capabilities": ["service_desk.access"],
        },
    )
    assert created.status_code == 201, created.text
    user = created.json()
    assert user["email"] == "patch-user@utmn.ru"
    assert user["display_name"] == "Patch User"
    assert user["department"] == "IT"

    assert client.patch(
        f"/admin/access/users/{user['id']}", json={"email": "abc"}
    ).status_code == 422
    assert client.patch(
        f"/admin/access/users/{user['id']}", json={"display_name": "   "}
    ).status_code == 422
    assert client.patch(
        f"/admin/access/users/{user['id']}",
        json={"capabilities": ["service_desk.manage_access"]},
    ).status_code == 422

    updated = client.patch(
        f"/admin/access/users/{user['id']}",
        json={
            "email": "  updated@utmn.ru ",
            "display_name": " Updated User ",
            "department": "   ",
            "position": " Lead ",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["email"] == "updated@utmn.ru"
    assert updated.json()["display_name"] == "Updated User"
    assert updated.json()["department"] is None
    assert updated.json()["position"] == "Lead"
    assert updated.json()["capabilities"] == ["service_desk.access"]

    replaced = client.put(
        f"/admin/access/users/{user['id']}/capabilities",
        json={"capabilities": ["service_desk.access", "service_desk.view_reports"]},
    )
    assert replaced.status_code == 200
    assert replaced.json()["capabilities"] == ["service_desk.access", "service_desk.view_reports"]

    with db_session_factory() as db:
        events = db.scalars(
            select(ServiceDeskAccessAuditEvent)
            .where(ServiceDeskAccessAuditEvent.target_user_id == uuid.UUID(user["id"]))
            .order_by(ServiceDeskAccessAuditEvent.created_at)
        ).all()
        assert [event.event_type for event in events] == [
            "access_user_created",
            "access_profile_updated",
            "capabilities_replaced",
        ]
        assert events[-1].before_state["capabilities"] == ["service_desk.access"]
        assert events[-1].after_state["capabilities"] == [
            "service_desk.access",
            "service_desk.view_reports",
        ]


def test_last_active_service_desk_admin_is_protected(client):
    page = client.get("/admin/access/users?access_type=service_desk_admin")
    assert page.status_code == 200, page.text
    only_admin = page.json()["items"][0]

    deactivated = client.post(f"/admin/access/users/{only_admin['id']}/deactivate")
    assert deactivated.status_code == 409
    assert deactivated.json()["detail"] == (
        "Нельзя отключить последнего активного администратора Service Desk"
    )

    demoted = client.patch(
        f"/admin/access/users/{only_admin['id']}",
        json={"access_type": "service_desk_manager"},
    )
    assert demoted.status_code == 409

    second_admin = client.post(
        "/admin/access/users",
        json={
            "identity_user_id": str(uuid.uuid4()),
            "email": "second-admin@utmn.ru",
            "display_name": "Second Admin",
            "access_type": "service_desk_admin",
        },
    )
    assert second_admin.status_code == 201, second_admin.text
    allowed = client.post(
        f"/admin/access/users/{second_admin.json()['id']}/deactivate"
    )
    assert allowed.status_code == 200
