import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.enums import (
    ServiceDeskAccessType,
    ServiceDeskTicketAction,
    ServiceDeskTicketStatus,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.tickets.lifecycle import CANCELLABLE_STATUSES, TicketLifecycleService, transition_target
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.tickets.repository import TicketRepository


TRANSITION_CASES = [
    (ServiceDeskTicketStatus.DRAFT, ServiceDeskTicketAction.SUBMIT, ServiceDeskTicketStatus.SUBMITTED),
    (
        ServiceDeskTicketStatus.SUBMITTED,
        ServiceDeskTicketAction.START_APPROVAL,
        ServiceDeskTicketStatus.PENDING_APPROVAL,
    ),
    (
        ServiceDeskTicketStatus.SUBMITTED,
        ServiceDeskTicketAction.SKIP_APPROVAL,
        ServiceDeskTicketStatus.APPROVED,
    ),
    (
        ServiceDeskTicketStatus.PENDING_APPROVAL,
        ServiceDeskTicketAction.COMPLETE_APPROVAL,
        ServiceDeskTicketStatus.APPROVED,
    ),
    (
        ServiceDeskTicketStatus.PENDING_APPROVAL,
        ServiceDeskTicketAction.REJECT_APPROVAL,
        ServiceDeskTicketStatus.REJECTED,
    ),
    (
        ServiceDeskTicketStatus.APPROVED,
        ServiceDeskTicketAction.ASSIGN,
        ServiceDeskTicketStatus.ASSIGNED,
    ),
    (
        ServiceDeskTicketStatus.ASSIGNED,
        ServiceDeskTicketAction.START,
        ServiceDeskTicketStatus.IN_PROGRESS,
    ),
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.REQUEST_CLARIFICATION,
        ServiceDeskTicketStatus.WAITING_REQUESTER,
    ),
    (
        ServiceDeskTicketStatus.WAITING_REQUESTER,
        ServiceDeskTicketAction.REQUESTER_REPLY,
        ServiceDeskTicketStatus.IN_PROGRESS,
    ),
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.WAIT_EXTERNAL,
        ServiceDeskTicketStatus.WAITING_EXTERNAL,
    ),
    (
        ServiceDeskTicketStatus.WAITING_EXTERNAL,
        ServiceDeskTicketAction.RESUME,
        ServiceDeskTicketStatus.IN_PROGRESS,
    ),
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.RESOLVE,
        ServiceDeskTicketStatus.RESOLVED,
    ),
    (
        ServiceDeskTicketStatus.RESOLVED,
        ServiceDeskTicketAction.CLOSE,
        ServiceDeskTicketStatus.CLOSED,
    ),
] + [
    (status, ServiceDeskTicketAction.CANCEL, ServiceDeskTicketStatus.CANCELLED)
    for status in CANCELLABLE_STATUSES
]


@pytest.mark.parametrize(("current_status", "action", "expected_status"), TRANSITION_CASES)
def test_transition_matrix_allows_defined_actions(current_status, action, expected_status):
    assert transition_target(current_status, action) == expected_status


@pytest.mark.parametrize(
    ("current_status", "action"),
    [
        (ServiceDeskTicketStatus.DRAFT, ServiceDeskTicketAction.START),
        (ServiceDeskTicketStatus.SUBMITTED, ServiceDeskTicketAction.RESOLVE),
        (ServiceDeskTicketStatus.REJECTED, ServiceDeskTicketAction.CANCEL),
        (ServiceDeskTicketStatus.RESOLVED, ServiceDeskTicketAction.CANCEL),
        (ServiceDeskTicketStatus.CLOSED, ServiceDeskTicketAction.CLOSE),
    ],
)
def test_transition_matrix_rejects_invalid_actions(current_status, action):
    assert transition_target(current_status, action) is None


def create_user(
    db_session_factory,
    email: str,
    *,
    access_type: ServiceDeskAccessType = ServiceDeskAccessType.MANAGER,
) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=email,
            display_name=email.split("@", 1)[0],
            access_type=access_type,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return str(user.id)


def create_submitted_ticket(
    client: TestClient,
    db_session_factory,
) -> tuple[str, str]:
    requester_id = create_user(db_session_factory, "lifecycle-requester@utmn.ru")
    category = client.post("/admin/categories", json={"title": "Lifecycle"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Lifecycle service"},
    )
    version = client.post(
        f"/admin/services/{service.json()['id']}/versions",
        json={"system_settings": {"is_description_required": False}},
    )
    published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
    assert published.status_code == 200, published.text
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "requester_user_id": requester_id,
            "title": "Lifecycle ticket",
        },
    )
    assert draft.status_code == 201, draft.text
    submitted = client.post(f"/tickets/{draft.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    return submitted.json()["id"], requester_id


def assign_ticket(db_session_factory, ticket_id: str, assignee_user_id: str) -> None:
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(ticket_id))
        assert ticket is not None
        ticket.status = ServiceDeskTicketStatus.ASSIGNED
        ticket.assignee_user_id = uuid.UUID(assignee_user_id)
        db.commit()


def test_lifecycle_action_endpoints_write_timestamps_and_history(client, db_session_factory):
    ticket_id, requester_id = create_submitted_ticket(client, db_session_factory)
    assignee_id = create_user(db_session_factory, "lifecycle-assignee@utmn.ru")
    assign_ticket(db_session_factory, ticket_id, assignee_id)

    foreign_start = client.post(
        f"/tickets/{ticket_id}/start",
        json={"actor_user_id": requester_id},
    )
    assert foreign_start.status_code == 403

    started = client.post(
        f"/tickets/{ticket_id}/start",
        json={"actor_user_id": assignee_id},
    )
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "in_progress"
    assert started.json()["work_started_at"] is not None

    duplicate_start = client.post(
        f"/tickets/{ticket_id}/start",
        json={"actor_user_id": assignee_id},
    )
    assert duplicate_start.status_code == 409

    clarification = client.post(
        f"/tickets/{ticket_id}/request-clarification",
        json={"actor_user_id": assignee_id, "comment": "Уточните количество участников"},
    )
    assert clarification.status_code == 200, clarification.text
    assert clarification.json()["status"] == "waiting_requester"

    with db_session_factory() as db:
        repository = TicketRepository(db)
        ticket = repository.get_ticket_for_update(uuid.UUID(ticket_id))
        requester = db.get(ServiceDeskUser, uuid.UUID(requester_id))
        assert ticket is not None and requester is not None
        TicketLifecycleService(repository).perform_transition(
            ticket,
            ServiceDeskTicketAction.REQUESTER_REPLY,
            actor=requester,
            metadata={"comment": "Участников будет десять"},
        )
        db.commit()

    waiting = client.post(
        f"/tickets/{ticket_id}/wait-external",
        json={"actor_user_id": assignee_id, "reason": "Ожидаем подтверждение аудитории"},
    )
    assert waiting.status_code == 200, waiting.text
    assert waiting.json()["status"] == "waiting_external"

    resumed = client.post(
        f"/tickets/{ticket_id}/resume",
        json={"actor_user_id": assignee_id},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["status"] == "in_progress"

    resolved = client.post(
        f"/tickets/{ticket_id}/resolve",
        json={
            "actor_user_id": assignee_id,
            "resolution_summary": "Аудитория забронирована",
            "comment": "Подтверждение получено",
        },
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolution_summary"] == "Аудитория забронирована"
    assert resolved.json()["resolved_at"] is not None

    closed = client.post(
        f"/tickets/{ticket_id}/close",
        json={"actor_user_id": requester_id},
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "closed"
    assert closed.json()["closed_at"] is not None
    assert [item["event_type"] for item in closed.json()["history"]][-7:] == [
        "ticket_started",
        "clarification_requested",
        "requester_replied",
        "ticket_waiting_external",
        "ticket_resumed",
        "ticket_resolved",
        "ticket_closed",
    ]


def test_requester_can_cancel_submitted_ticket_with_reason(client, db_session_factory):
    ticket_id, requester_id = create_submitted_ticket(client, db_session_factory)
    foreign_user_id = create_user(db_session_factory, "foreign-manager@utmn.ru")

    forbidden = client.post(
        f"/tickets/{ticket_id}/cancel",
        json={"actor_user_id": foreign_user_id, "reason": "Не моя заявка"},
    )
    assert forbidden.status_code == 403

    cancelled = client.post(
        f"/tickets/{ticket_id}/cancel",
        json={"actor_user_id": requester_id, "reason": "Потребность отпала"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancellation_reason"] == "Потребность отпала"
    assert cancelled.json()["cancelled_at"] is not None
    assert cancelled.json()["history"][-1]["event_type"] == "ticket_cancelled"
