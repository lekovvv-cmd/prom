import uuid
from datetime import UTC, datetime

from sqlalchemy import event

from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus
from app.core.enums import ServiceDeskAccessType
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.tickets.models import ServiceDeskTicket


def _manager(db_session_factory, auth_headers_for_user, *capabilities):
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email="reports@utmn.ru",
            display_name="Reports",
            access_type=ServiceDeskAccessType.MANAGER,
        )
        db.add(user)
        db.flush()
        db.add_all(
            [
                ServiceDeskUserCapability(service_desk_user_id=user.id, capability=value)
                for value in ("service_desk.access", *capabilities)
            ]
        )
        db.commit()
        user_id = str(user.id)
    return auth_headers_for_user(user_id)


def test_stats_authorization_and_empty_contract(client, db_session_factory, auth_headers_for_user):
    assert client.get("/admin/stats/summary", headers={}).status_code == 401
    forbidden = _manager(db_session_factory, auth_headers_for_user)
    assert client.get("/admin/stats/summary", headers=forbidden).status_code == 403
    reports = _manager(db_session_factory, auth_headers_for_user, "service_desk.view_reports")
    response = client.get("/admin/stats/summary", headers=reports)
    assert response.status_code == 200
    assert response.json()["current_backlog"] == 0
    times = client.get("/admin/stats/times", headers=reports).json()
    assert times["time_to_approval"] == {
        "average_seconds": None,
        "median_seconds": None,
        "p90_seconds": None,
        "sample_size": 0,
    }
    assert (
        client.get(
            "/admin/stats/summary?date_from=2026-07-12&date_to=2026-07-11", headers=reports
        ).status_code
        == 422
    )


def _service(db):
    category = ServiceDeskCategory(title="IT")
    db.add(category)
    db.flush()
    service = ServiceDeskService(category_id=category.id, title="Network")
    db.add(service)
    db.flush()
    return service


def _user(db, name="Assignee", *, reports=False):
    user = ServiceDeskUser(
        identity_user_id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@utmn.ru",
        display_name=name,
        access_type=ServiceDeskAccessType.MANAGER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    caps = ["service_desk.access"]
    if reports:
        caps.append("service_desk.view_reports")
    db.add_all([
        ServiceDeskUserCapability(service_desk_user_id=user.id, capability=cap)
        for cap in caps
    ])
    db.flush()
    return user


def _ticket(db, service, requester, assignee, **values):
    ticket = ServiceDeskTicket(
        service_id=service.id,
        template_version_id=uuid.uuid4(),
        requester_user_id=requester.id,
        assignee_user_id=assignee.id,
        title=values.pop("title", "Stats ticket"),
        status=values.pop("status", ServiceDeskTicketStatus.RESOLVED),
        priority=values.pop("priority", ServiceDeskPriority.MEDIUM),
        field_values={},
        submitted_at=values.pop("submitted_at", datetime(2026, 7, 9, tzinfo=UTC)),
        **values,
    )
    db.add(ticket)
    db.flush()
    return ticket


def test_sla_compliance_uses_completed_obligation_cohort_and_event_counters(
    client, db_session_factory, auth_headers_for_user
):
    with db_session_factory() as db:
        service = _service(db)
        requester = _user(db, "Requester")
        assignee = _user(db, "Assignee", reports=True)
        _ticket(
            db,
            service,
            requester,
            assignee,
            first_response_at=datetime(2026, 7, 11, 10, tzinfo=UTC),
            response_breached_at=datetime(2026, 7, 10, 10, tzinfo=UTC),
            is_response_breached=True,
            resolved_at=datetime(2026, 7, 11, 12, tzinfo=UTC),
            resolution_breached_at=datetime(2026, 7, 10, 12, tzinfo=UTC),
            is_resolution_breached=True,
            sla_snapshot={"policy": "same-cohort"},
        )
        _ticket(
            db,
            service,
            requester,
            assignee,
            first_response_at=datetime(2026, 7, 11, 11, tzinfo=UTC),
            resolved_at=datetime(2026, 7, 11, 13, tzinfo=UTC),
            sla_snapshot={"policy": "same-cohort"},
        )
        db.commit()
        headers = auth_headers_for_user(str(assignee.id))

    day_b = client.get(
        "/admin/stats/sla?date_from=2026-07-11&date_to=2026-07-11",
        headers=headers,
    )
    assert day_b.status_code == 200, day_b.text
    assert day_b.json()["response_compliance_percent"] == 50
    assert day_b.json()["resolution_compliance_percent"] == 50
    assert day_b.json()["response_breaches"] == 0
    assert day_b.json()["resolution_breaches"] == 0

    day_a = client.get(
        "/admin/stats/sla?date_from=2026-07-10&date_to=2026-07-10",
        headers=headers,
    ).json()
    assert day_a["response_compliance_percent"] is None
    assert day_a["resolution_compliance_percent"] is None
    assert day_a["response_breaches"] == 1
    assert day_a["resolution_breaches"] == 1


def test_assignee_stats_are_set_based_and_do_not_double_count_breached_ticket(
    client, db_session_factory, auth_headers_for_user
):
    with db_session_factory() as db:
        service = _service(db)
        requester = _user(db, "Requester")
        reports = _user(db, "Reports", reports=True)
        assignees = [_user(db, f"Assignee {index}") for index in range(10)]
        _ticket(
            db,
            service,
            requester,
            assignees[0],
            status=ServiceDeskTicketStatus.IN_PROGRESS,
            submitted_at=datetime(2026, 7, 11, 9, tzinfo=UTC),
            first_response_at=datetime(2026, 7, 11, 10, tzinfo=UTC),
            resolved_at=datetime(2026, 7, 11, 12, tzinfo=UTC),
            response_breached_at=datetime(2026, 7, 11, 9, tzinfo=UTC),
            resolution_breached_at=datetime(2026, 7, 11, 11, tzinfo=UTC),
        )
        for assignee in assignees[1:]:
            _ticket(
                db,
                service,
                requester,
                assignee,
                status=ServiceDeskTicketStatus.ASSIGNED,
            )
        db.commit()
        headers = auth_headers_for_user(str(reports.id))
        engine = db.get_bind()

    statements: list[str] = []

    def before_cursor_execute(*args):
        statements.append(args[2])

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        response = client.get(
            "/admin/stats/assignees?date_from=2026-07-11&date_to=2026-07-11",
            headers=headers,
        )
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert response.status_code == 200, response.text
    assert len(statements) <= 8
    rows = {row["display_name"]: row for row in response.json()}
    assert rows["Assignee 0"]["currently_assigned"] == 1
    assert rows["Assignee 0"]["in_progress"] == 1
    assert rows["Assignee 0"]["breached_tickets"] == 1
    assert rows["Assignee 0"]["median_resolution_seconds"] == 10800
