import uuid
from datetime import UTC, datetime, timedelta

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.sla.worker import SlaWorker
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from sqlalchemy import select


def create_sla_user(
    client,
    db_session_factory,
    *,
    can_manage_sla: bool,
    has_service_desk_access: bool = True,
    access_type: ServiceDeskAccessType = ServiceDeskAccessType.MANAGER,
) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=f"sla-{uuid.uuid4().hex}@utmn.ru",
            display_name="SLA administrator",
            access_type=access_type,
            is_active=True,
        )
        db.add(user)
        db.flush()
        capabilities = ["service_desk.access"] if has_service_desk_access else []
        if can_manage_sla:
            capabilities.append("service_desk.manage_sla")
        for capability in capabilities:
            db.add(ServiceDeskUserCapability(service_desk_user_id=user.id, capability=capability))
        db.commit()
        return str(user.id)


def test_sla_authorization_uses_central_service_desk_capability_semantics(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    ordinary_user_id = create_sla_user(
        client,
        db_session_factory,
        can_manage_sla=False,
        has_service_desk_access=False,
    )
    manager_id = create_sla_user(client, db_session_factory, can_manage_sla=False)
    capability_holder_id = create_sla_user(client, db_session_factory, can_manage_sla=True)
    service_desk_admin_id = create_sla_user(
        client,
        db_session_factory,
        can_manage_sla=False,
        access_type=ServiceDeskAccessType.SERVICE_DESK_ADMIN,
    )

    assert client.get("/admin/sla/calendars", headers={}).status_code == 401
    assert (
        client.get(
            "/admin/sla/calendars",
            headers=auth_headers_for_user(ordinary_user_id),
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/admin/sla/calendars",
            headers=auth_headers_for_user(manager_id),
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/admin/sla/calendars",
            headers=auth_headers_for_user(capability_holder_id),
        ).status_code
        == 200
    )
    admin_headers = auth_headers_for_user(service_desk_admin_id)
    assert client.get("/admin/sla/calendars", headers=admin_headers).status_code == 200

    calendar = client.post(
        "/admin/sla/calendars",
        json={
            "name": "Authorization calendar",
            "timezone": "Asia/Yekaterinburg",
            "business_hours": [
                {"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}
            ],
        },
        headers=auth_headers_for_user(capability_holder_id),
    )
    assert calendar.status_code == 201, calendar.text

    manager_policy = client.post(
        "/admin/sla/policies",
        json={
            "name": "Forbidden manager policy",
            "business_calendar_id": calendar.json()["id"],
            "first_response_minutes": 30,
            "resolution_minutes": 240,
        },
        headers=auth_headers_for_user(manager_id),
    )
    assert manager_policy.status_code == 403

    admin_policy = client.post(
        "/admin/sla/policies",
        json={
            "name": "Service Desk admin policy",
            "business_calendar_id": calendar.json()["id"],
            "first_response_minutes": 30,
            "resolution_minutes": 240,
        },
        headers=admin_headers,
    )
    assert admin_policy.status_code == 201, admin_policy.text


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
    assert [item["start_time"] for item in calendar["business_hours"]] == [
        "09:00:00",
        "14:00:00",
        "09:00:00",
    ]

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
    assert [
        (item["weekday"], item["start_time"], item["end_time"])
        for item in updated.json()["business_hours"]
    ] == [(5, "10:00:00", "16:00:00")]

    invalid_timezone = client.post(
        "/admin/sla/calendars",
        json={**payload, "name": "Invalid timezone", "timezone": "Mars/Olympus"},
        headers=admin_headers,
    )
    assert invalid_timezone.status_code == 422


def test_calendar_exceptions_are_validated_and_replaced(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    admin_id = create_sla_user(client, db_session_factory, can_manage_sla=True)
    admin_headers = auth_headers_for_user(admin_id)
    payload = {
        "name": "Calendar with exceptions",
        "timezone": "Asia/Yekaterinburg",
        "business_hours": [{"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}],
        "exceptions": [
            {
                "date": "2026-12-31",
                "type": "holiday",
                "description": "New Year holiday",
            },
            {
                "date": "2027-01-09",
                "type": "custom_hours",
                "start_time": "10:00:00",
                "end_time": "13:00:00",
            },
            {
                "date": "2027-01-09",
                "type": "custom_hours",
                "start_time": "14:00:00",
                "end_time": "16:00:00",
            },
        ],
    }

    created = client.post("/admin/sla/calendars", json=payload, headers=admin_headers)
    assert created.status_code == 201, created.text
    calendar = created.json()
    assert [(item["date"], item["type"]) for item in calendar["exceptions"]] == [
        ("2026-12-31", "holiday"),
        ("2027-01-09", "custom_hours"),
        ("2027-01-09", "custom_hours"),
    ]

    mixed_types = client.patch(
        f"/admin/sla/calendars/{calendar['id']}",
        json={
            "exceptions": [
                {"date": "2027-01-10", "type": "working_day"},
                {
                    "date": "2027-01-10",
                    "type": "custom_hours",
                    "start_time": "10:00:00",
                    "end_time": "16:00:00",
                },
            ]
        },
        headers=admin_headers,
    )
    assert mixed_types.status_code == 422

    invalid_holiday_times = client.patch(
        f"/admin/sla/calendars/{calendar['id']}",
        json={
            "exceptions": [
                {
                    "date": "2027-01-10",
                    "type": "holiday",
                    "start_time": "10:00:00",
                }
            ]
        },
        headers=admin_headers,
    )
    assert invalid_holiday_times.status_code == 422

    replaced = client.patch(
        f"/admin/sla/calendars/{calendar['id']}",
        json={"exceptions": [{"date": "2027-01-10", "type": "working_day"}]},
        headers=admin_headers,
    )
    assert replaced.status_code == 200, replaced.text
    assert [(item["date"], item["type"]) for item in replaced.json()["exceptions"]] == [
        ("2027-01-10", "working_day")
    ]


def test_sla_policy_binding_is_snapshotted_on_submit(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    requester_id = create_sla_user(client, db_session_factory, can_manage_sla=True)
    headers = auth_headers_for_user(requester_id)
    calendar = client.post(
        "/admin/sla/calendars",
        json={
            "name": "Support calendar",
            "timezone": "Asia/Yekaterinburg",
            "business_hours": [{"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}],
        },
        headers=headers,
    )
    assert calendar.status_code == 201, calendar.text
    policy = client.post(
        "/admin/sla/policies",
        json={
            "name": "High priority policy",
            "business_calendar_id": calendar.json()["id"],
            "first_response_minutes": 30,
            "resolution_minutes": 240,
        },
        headers=headers,
    )
    assert policy.status_code == 201, policy.text
    escalation = client.post(
        f"/admin/sla/policies/{policy.json()['id']}/escalations",
        json={
            "metric": "resolution",
            "threshold_percent": 87,
            "action_type": "create_in_app_notification",
            "recipient_type": "assignee",
        },
        headers=headers,
    )
    assert escalation.status_code == 201, escalation.text
    assert escalation.json()["threshold_percent"] == 87
    category = client.post("/admin/categories", json={"title": "SLA category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "SLA service"},
    )
    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    client.post(
        f"/admin/template-versions/{version.json()['id']}/fields",
        json={
            "key": "impact",
            "label": "Impact",
            "field_type": "text",
            "is_required": True,
            "position": 0,
        },
    )
    published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
    assert published.status_code == 200, published.text
    binding = client.post(
        "/admin/sla/bindings",
        json={
            "policy_id": policy.json()["id"],
            "name": "Critical impact",
            "priority": 10,
            "conditions": [
                {"field": "service_id", "value": service.json()["id"]},
                {"field": "priority", "value": "high"},
                {"field": "field_value", "field_key": "impact", "value": "critical"},
            ],
        },
        headers=headers,
    )
    assert binding.status_code == 201, binding.text
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "title": "Critical incident",
            "description": "Critical incident description",
            "priority": "high",
            "field_values": {"impact": "critical"},
        },
        headers=headers,
    )
    submitted = client.post(f"/tickets/{draft.json()['id']}/submit", headers=headers)
    assert submitted.status_code == 200, submitted.text
    snapshot = submitted.json()["sla_snapshot"]
    assert snapshot["policy_id"] == policy.json()["id"]
    assert snapshot["binding_id"] == binding.json()["id"]
    assert snapshot["first_response_minutes"] == 30

    changed = client.patch(
        f"/admin/sla/policies/{policy.json()['id']}",
        json={"first_response_minutes": 5},
        headers=headers,
    )
    assert changed.status_code == 200
    details = client.get(f"/tickets/{draft.json()['id']}", headers=headers)
    assert details.json()["sla_snapshot"]["first_response_minutes"] == 30

    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(draft.json()["id"]))
        now = datetime.now(UTC)
        ticket.first_response_due_at = now - timedelta(minutes=1)
        ticket.resolution_due_at = now - timedelta(minutes=1)
        db.commit()
        first = SlaWorker(db).run_once(now=now)
        second = SlaWorker(db).run_once(now=now + timedelta(minutes=1))
        assert first["response_breaches"] == first["resolution_breaches"] == 1
        assert second["response_breaches"] == second["resolution_breaches"] == 0
        events = db.scalars(select(ServiceDeskTicketHistory).where(
            ServiceDeskTicketHistory.ticket_id == ticket.id,
            ServiceDeskTicketHistory.event_type == "sla_breached",
        )).all()
        assert {event.payload["metric"] for event in events} == {"first_response", "resolution"}


def test_specific_user_escalation_requires_active_service_desk_recipient(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    admin_id = create_sla_user(client, db_session_factory, can_manage_sla=True)
    recipient_id = create_sla_user(client, db_session_factory, can_manage_sla=False)
    headers = auth_headers_for_user(admin_id)
    calendar = client.post(
        "/admin/sla/calendars",
        json={
            "name": "Escalation recipient calendar",
            "timezone": "Asia/Yekaterinburg",
            "business_hours": [
                {"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}
            ],
        },
        headers=headers,
    )
    policy = client.post(
        "/admin/sla/policies",
        json={
            "name": "Escalation recipient policy",
            "business_calendar_id": calendar.json()["id"],
            "first_response_minutes": 30,
            "resolution_minutes": 240,
        },
        headers=headers,
    )

    recipients = client.get("/admin/sla/recipients", headers=headers)
    assert recipients.status_code == 200, recipients.text
    assert recipient_id in {item["id"] for item in recipients.json()}

    created = client.post(
        f"/admin/sla/policies/{policy.json()['id']}/escalations",
        json={
            "metric": "resolution",
            "threshold_percent": 73,
            "action_type": "create_in_app_notification",
            "recipient_type": "specific_user",
            "recipient_user_id": recipient_id,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text

    invalid_update = client.patch(
        f"/admin/sla/escalations/{created.json()['id']}",
        json={"recipient_type": "specific_user", "recipient_user_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert invalid_update.status_code == 422

    cleared = client.patch(
        f"/admin/sla/escalations/{created.json()['id']}",
        json={"recipient_type": "requester", "recipient_user_id": None},
        headers=headers,
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["recipient_type"] == "requester"
    assert cleared.json()["recipient_user_id"] is None
