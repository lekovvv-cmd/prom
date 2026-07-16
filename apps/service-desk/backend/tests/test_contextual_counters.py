import uuid
from datetime import UTC, datetime

from app.core.enums import (
    ApprovalDecisionRule,
    ServiceDeskApprovalStatus,
    ServiceDeskTicketStatus,
)
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.tickets.models import ServiceDeskTicket
from test_lifecycle import create_submitted_ticket


def test_contextual_counters_are_actor_aware(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, actor_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    with db_session_factory() as db:
        source = db.get(ServiceDeskTicket, uuid.UUID(ticket_id))
        source.status = ServiceDeskTicketStatus.PENDING_APPROVAL
        stage = ServiceDeskTicketApprovalStage(
            ticket_id=source.id, position=0, title="Counter approval",
            decision_rule=ApprovalDecisionRule.ANY,
            status=ServiceDeskApprovalStatus.PENDING, started_at=datetime.now(UTC),
        )
        db.add(stage)
        db.flush()
        db.add(ServiceDeskTicketApproval(
            ticket_approval_stage_id=stage.id, approver_user_id=uuid.UUID(actor_id),
            status=ServiceDeskApprovalStatus.PENDING,
        ))
        for status, assignee in [
            (ServiceDeskTicketStatus.ASSIGNED, uuid.UUID(actor_id)),
            (ServiceDeskTicketStatus.WAITING_REQUESTER, None),
        ]:
            db.add(ServiceDeskTicket(
                service_id=source.service_id, template_version_id=source.template_version_id,
                requester_user_id=uuid.UUID(actor_id), assignee_user_id=assignee,
                title=f"Counter {status.value}", status=status,
            ))
        db.commit()

    response = client.get(
        "/notifications/contextual-counters", headers=auth_headers_for_user(actor_id)
    )
    assert response.status_code == 200
    assert response.json() == {
        "waiting_my_approval": 1,
        "assigned_to_me": 1,
        "awaiting_my_response": 1,
        "sla_breaches": None,
    }
    assert client.get("/notifications/contextual-counters").status_code == 401


def test_sla_counter_requires_capability_and_respects_admin_view(
    client, db_session_factory, auth_headers_for_user
):
    ticket_id, actor_id = create_submitted_ticket(client, db_session_factory, auth_headers_for_user)
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(ticket_id))
        ticket.is_resolution_breached = True
        db.commit()

    regular = client.get(
        "/notifications/contextual-counters", headers=auth_headers_for_user(actor_id)
    )
    assert regular.json()["sla_breaches"] is None
    admin = client.get("/notifications/contextual-counters", headers=client.admin_headers)
    assert admin.status_code == 200
    assert admin.json()["sla_breaches"] == 1
