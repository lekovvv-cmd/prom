import uuid

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def create_sla_user(client, db_session_factory, *, can_manage_sla: bool) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=f"sla-{uuid.uuid4().hex}@utmn.ru",
            display_name="SLA administrator",
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(user)
        db.flush()
        capabilities = ["service_desk.access"]
        if can_manage_sla:
            capabilities.append("service_desk.manage_sla")
        for capability in capabilities:
            db.add(ServiceDeskUserCapability(service_desk_user_id=user.id, capability=capability))
        db.commit()
        return str(user.id)


def test_business_calendars_require_capability_and_validate_working_intervals(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    reader_id = create_sla_user(client, db_session_factory, can_manage_sla=False)
    admin_id = create_sla_user(client, db_session_factory, can_manage_sla=True)
    reader_headers = auth_headers_for_user(reader_id)
    admin_headers = auth_headers_for_user(admin_id)
    payload = {
        "name": "Tyumen weekday schedule",
        "timezone": "Asia/Yekaterinburg",
        "business_hours": [
            {"weekday": 0, "start_time": "09:00:00", "end_time": "13:00:00"},
            {"weekday": 0, "start_time": "14:00:00", "end_time": "18:00:00"},
            {"weekday": 1, "start_time": "09:00:00", "end_time": "18:00:00"},
        ],
    }

    forbidden = client.post("/admin/sla/calendars", json=payload, headers=reader_headers)
    assert forbidden.status_code == 403

    created = client.post("/admin/sla/calendars", json=payload, headers=admin_headers)
    assert created.status_code == 201, created.text
    calendar = created.json()
    assert calendar["timezone"] == "Asia/Yekaterinburg"
    assert [item["start_time"] for item in calendar["business_hours"]] == ["09:00:00", "14:00:00", "09:00:00"]

    listed = client.get("/admin/sla/calendars", headers=admin_headers)
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [calendar["id"]]

    overlapping = client.patch(
        f"/admin/sla/calendars/{calendar['id']}",
        json={
            "business_hours": [
                {"weekday": 0, "start_time": "09:00:00", "end_time": "13:00:00"},
                {"weekday": 0, "start_time": "12:30:00", "end_time": "18:00:00"},
            ]
        },
        headers=admin_headers,
    )
    assert overlapping.status_code == 422

    updated = client.patch(
        f"/admin/sla/calendars/{calendar['id']}",
        json={
            "name": "Weekend support",
            "is_active": False,
            "business_hours": [{"weekday": 5, "start_time": "10:00:00", "end_time": "16:00:00"}],
        },
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Weekend support"
    assert updated.json()["is_active"] is False
    assert [(item["weekday"], item["start_time"], item["end_time"]) for item in updated.json()["business_hours"]] == [
        (5, "10:00:00", "16:00:00")
    ]

    invalid_timezone = client.post(
        "/admin/sla/calendars",
        json={**payload, "name": "Invalid timezone", "timezone": "Mars/Olympus"},
        headers=admin_headers,
    )
    assert invalid_timezone.status_code == 422
