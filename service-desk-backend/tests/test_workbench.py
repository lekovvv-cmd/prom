import uuid
from datetime import UTC, datetime, timedelta

from app.core.enums import ServiceDeskAccessType, ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.tickets.policy import TicketPolicyService
from app.modules.sla.models import (
    ServiceDeskEscalationRule,
    ServiceDeskSlaEscalationEvent,
    ServiceDeskTicketSlaPause,
)
from test_tickets import create_requester, create_service_with_template


def create_manager(db_session_factory, *capabilities: str) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=f"{uuid.uuid4()}@utmn.ru",
            display_name="Операционный менеджер",
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(user)
        db.flush()
        for capability in ("service_desk.access", *capabilities):
            db.add(ServiceDeskUserCapability(
                service_desk_user_id=user.id, capability=capability
            ))
        db.commit()
        return str(user.id)


def add_ticket(db_session_factory, source_id: str, **values) -> str:
    with db_session_factory() as db:
        source = db.get(ServiceDeskTicket, uuid.UUID(source_id))
        ticket = ServiceDeskTicket(
            service_id=source.service_id,
            template_version_id=source.template_version_id,
            requester_user_id=values.pop("requester_user_id", source.requester_user_id),
            title=values.pop("title", "Заявка Workbench"),
            status=values.pop("status", ServiceDeskTicketStatus.SUBMITTED),
            **values,
        )
        db.add(ticket)
        db.commit()
        return str(ticket.id)


def test_workbench_access_visibility_and_draft_privacy(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    service_id, _ = create_service_with_template(client)
    draft = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Чужой черновик", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    requester_only = create_manager(db_session_factory, "service_desk.create_request")
    operator = create_manager(db_session_factory, "service_desk.be_assignee")

    assert client.get("/workbench/tickets").status_code == 401
    assert client.get(
        "/workbench/tickets", headers=auth_headers_for_user(requester_only)
    ).status_code == 403
    response = client.get(
        "/workbench/tickets", headers=auth_headers_for_user(operator)
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    admin = client.get("/workbench/tickets", headers=client.admin_headers)
    assert admin.status_code == 200
    assert draft["id"] not in {item["ticket_id"] for item in admin.json()["items"]}


def test_workbench_filters_search_pagination_and_sla(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee")
    service_id, _ = create_service_with_template(client)
    created = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Сетевая заявка", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(created["id"]))
        ticket.number = "SD-2026-000042"
        ticket.status = ServiceDeskTicketStatus.IN_PROGRESS
        ticket.priority = ServiceDeskPriority.CRITICAL
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "test"}
        ticket.first_response_due_at = datetime.now(UTC) - timedelta(minutes=5)
        db.commit()
    add_ticket(
        db_session_factory,
        created["id"],
        requester_user_id=uuid.UUID(operator_id),
        title="Вторая заявка",
        status=ServiceDeskTicketStatus.ASSIGNED,
    )
    headers = auth_headers_for_user(operator_id)
    params = {
        "status": "in_progress",
        "assignee_user_id": operator_id,
        "requester_user_id": requester_id,
        "priority": "critical",
        "service_id": service_id,
        "sla_state": "breached",
        "overdue": "true",
        "q": "000042",
    }
    response = client.get("/workbench/tickets", params=params, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["sla"]["state"] == "breached"
    assert client.get(
        "/workbench/tickets", params={"q": "Сетевая"}, headers=headers
    ).json()["total"] == 1
    assert client.get(
        "/workbench/tickets", params={"q": "Бронирование"}, headers=headers
    ).json()["total"] == 2
    first = client.get(
        "/workbench/tickets", params={"page_size": 1}, headers=headers
    ).json()
    second = client.get(
        "/workbench/tickets", params={"page_size": 1, "page": 2}, headers=headers
    ).json()
    assert first["total"] == 2
    assert first["items"][0]["ticket_id"] != second["items"][0]["ticket_id"]
    assert client.get(
        "/workbench/tickets",
        params={"created_from": "2026-02-02T00:00:00Z", "created_to": "2026-01-01T00:00:00Z"},
        headers=headers,
    ).status_code == 422


def test_workbench_counters_match_quick_views(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Источник", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    add_ticket(
        db_session_factory,
        source["id"],
        assignee_user_id=uuid.UUID(operator_id),
        status=ServiceDeskTicketStatus.IN_PROGRESS,
    )
    add_ticket(
        db_session_factory,
        source["id"],
        requester_user_id=uuid.UUID(operator_id),
        status=ServiceDeskTicketStatus.RESOLVED,
    )
    add_ticket(
        db_session_factory,
        source["id"],
        requester_user_id=uuid.UUID(operator_id),
        status=ServiceDeskTicketStatus.CLOSED,
    )
    headers = auth_headers_for_user(operator_id)
    counters = client.get("/workbench/counters", headers=headers)
    assert counters.status_code == 200
    assert counters.json()["in_progress"] == 1
    assert counters.json()["assigned_to_me"] == 1
    assert counters.json()["resolved"] == 1
    assert counters.json()["sla_breached"] is None
    for key, count in counters.json().items():
        if count is not None:
            result = client.get(
                "/workbench/tickets", params={"quick_view": key}, headers=headers
            )
            assert result.status_code == 200, result.text
            assert result.json()["total"] == count
    assert client.get(
        "/workbench/tickets", params={"page_size": 101}, headers=headers
    ).status_code == 422


def test_allowed_actions_match_lifecycle_and_assignee_options(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    assignee_id = create_manager(db_session_factory, "service_desk.be_assignee")
    inactive_id = create_manager(db_session_factory, "service_desk.be_assignee")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Матрица действий", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.ASSIGNED
        ticket.assignee_user_id = uuid.UUID(assignee_id)
        db.get(ServiceDeskUser, uuid.UUID(inactive_id)).is_active = False
        db.commit()
    headers = auth_headers_for_user(assignee_id)
    row = client.get("/workbench/tickets", headers=headers).json()["items"][0]
    assert row["allowed_actions"] == ["start"]
    started = client.post(f"/tickets/{source['id']}/start", json={}, headers=headers)
    assert started.status_code == 200
    assert {
        "request_clarification", "wait_external", "resolve"
    }.issubset(started.json()["allowed_actions"])
    options = client.get(
        "/workbench/users", params={"eligible_assignees": "true"}, headers=headers
    )
    assert options.status_code == 200
    option_ids = {item["id"] for item in options.json()}
    assert assignee_id in option_ids
    assert inactive_id not in option_ids

    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        unrelated = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()), email="unrelated@utmn.ru",
            display_name="Посторонний", access_type=ServiceDeskAccessType.MANAGER, is_active=True,
        )
        db.add(unrelated)
        db.flush()
        assert TicketPolicyService().allowed_actions(ticket, unrelated) == []


def add_warning_event(db, ticket: ServiceDeskTicket, metric: str) -> None:
    policy_id = ticket.sla_policy_id or uuid.uuid4()
    ticket.sla_policy_id = policy_id
    rule = ServiceDeskEscalationRule(
        sla_policy_id=policy_id,
        metric=metric,
        threshold_percent=80,
        action_type="history_only",
        recipient_type="requester",
        is_active=True,
    )
    db.add(rule)
    db.flush()
    db.add(ServiceDeskSlaEscalationEvent(
        ticket_id=ticket.id,
        rule_id=rule.id,
        metric=metric,
        action_type=rule.action_type,
        recipient_type=rule.recipient_type,
    ))


def test_workbench_sla_warning_uses_current_active_metric(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee", "service_desk.manage_sla")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Historical warning", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.IN_PROGRESS
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "warning"}
        ticket.first_response_at = datetime.now(UTC) - timedelta(minutes=5)
        ticket.resolution_due_at = datetime.now(UTC) + timedelta(hours=1)
        add_warning_event(db, ticket, "first_response")
        db.commit()
    headers = auth_headers_for_user(operator_id)
    response = client.get("/workbench/tickets", params={"sla_state": "warning"}, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 0
    row = client.get("/workbench/tickets", headers=headers).json()["items"][0]
    assert row["sla"]["metric"] == "resolution"
    assert row["sla"]["state"] == "on_track"


def test_workbench_sla_warning_ignores_resolved_compliant_ticket(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee", "service_desk.manage_sla")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Resolved warning", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.RESOLVED
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "warning"}
        ticket.first_response_at = datetime.now(UTC) - timedelta(hours=2)
        ticket.resolved_at = datetime.now(UTC) - timedelta(minutes=10)
        ticket.resolution_due_at = datetime.now(UTC) + timedelta(hours=1)
        add_warning_event(db, ticket, "resolution")
        db.commit()
    headers = auth_headers_for_user(operator_id)
    response = client.get("/workbench/tickets", params={"sla_state": "warning"}, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 0
    row = client.get("/workbench/tickets", headers=headers).json()["items"][0]
    assert row["sla"] == {"state": "on_track", "metric": None, "due_at": None}


def test_workbench_sla_active_metric_warning_and_breach_precedence(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee", "service_desk.manage_sla")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Active warning", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.IN_PROGRESS
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "warning"}
        ticket.first_response_at = datetime.now(UTC) - timedelta(hours=1)
        ticket.resolution_due_at = datetime.now(UTC) + timedelta(hours=1)
        add_warning_event(db, ticket, "resolution")
        db.commit()
    headers = auth_headers_for_user(operator_id)
    warning = client.get("/workbench/tickets", params={"sla_state": "warning"}, headers=headers).json()
    assert warning["total"] == 1
    assert warning["items"][0]["sla"]["state"] == "warning"

    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.is_resolution_breached = True
        db.commit()
    breached = client.get("/workbench/tickets", params={"sla_state": "breached"}, headers=headers).json()
    assert breached["total"] == 1
    assert breached["items"][0]["sla"]["state"] == "breached"
    assert client.get(
        "/workbench/tickets", params={"sla_state": "warning"}, headers=headers
    ).json()["total"] == 0


def test_workbench_first_response_sla_ignores_resolution_pause(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "SLA pause", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.WAITING_EXTERNAL
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "pause"}
        ticket.first_response_due_at = datetime.now(UTC) - timedelta(hours=1)
        db.add(ServiceDeskTicketSlaPause(
            ticket_id=ticket.id,
            reason_status=ServiceDeskTicketStatus.WAITING_EXTERNAL.value,
            started_at=datetime.now(UTC) - timedelta(hours=2),
        ))
        db.commit()
    headers = auth_headers_for_user(operator_id)
    breached = client.get(
        "/workbench/tickets", params={"sla_state": "breached"}, headers=headers
    ).json()
    assert breached["total"] == 1
    assert breached["items"][0]["sla"]["metric"] == "first_response"
    assert breached["items"][0]["sla"]["state"] == "breached"
    assert client.get(
        "/workbench/tickets", params={"overdue": "true"}, headers=headers
    ).json()["total"] == 1
    assert client.get(
        "/workbench/tickets", params={"sla_state": "paused"}, headers=headers
    ).json()["total"] == 0


def test_workbench_resolution_sla_pause_overrides_objective_overdue(
    client, db_session_factory, auth_headers_for_user
):
    requester_id = create_requester(client, db_session_factory)
    operator_id = create_manager(db_session_factory, "service_desk.be_assignee")
    service_id, _ = create_service_with_template(client)
    source = client.post(
        "/tickets/drafts",
        json={"service_id": service_id, "title": "Resolution pause", "field_values": {"room": "1"}},
        headers=auth_headers_for_user(requester_id),
    ).json()
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(source["id"]))
        ticket.status = ServiceDeskTicketStatus.WAITING_EXTERNAL
        ticket.assignee_user_id = uuid.UUID(operator_id)
        ticket.sla_snapshot = {"policy": "pause"}
        ticket.first_response_at = datetime.now(UTC) - timedelta(hours=2)
        ticket.resolution_due_at = datetime.now(UTC) - timedelta(hours=1)
        db.add(ServiceDeskTicketSlaPause(
            ticket_id=ticket.id,
            reason_status=ServiceDeskTicketStatus.WAITING_EXTERNAL.value,
            started_at=datetime.now(UTC) - timedelta(hours=2),
        ))
        db.commit()
    headers = auth_headers_for_user(operator_id)
    paused = client.get(
        "/workbench/tickets", params={"sla_state": "paused"}, headers=headers
    ).json()
    assert paused["total"] == 1
    assert paused["items"][0]["sla"]["state"] == "paused"
    assert paused["items"][0]["sla"]["metric"] == "resolution"
    assert client.get(
        "/workbench/tickets", params={"overdue": "true"}, headers=headers
    ).json()["total"] == 0
