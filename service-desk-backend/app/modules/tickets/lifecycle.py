from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.core.enums import (
    ServiceDeskAccessType,
    ServiceDeskTicketAction,
    ServiceDeskTicketStatus,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.repository import TicketRepository


REASSIGNABLE_STATUSES = {
    ServiceDeskTicketStatus.ASSIGNED,
    ServiceDeskTicketStatus.IN_PROGRESS,
    ServiceDeskTicketStatus.WAITING_REQUESTER,
    ServiceDeskTicketStatus.WAITING_EXTERNAL,
}


TRANSITION_TARGETS: dict[
    tuple[ServiceDeskTicketStatus, ServiceDeskTicketAction],
    ServiceDeskTicketStatus,
] = {
    (ServiceDeskTicketStatus.DRAFT, ServiceDeskTicketAction.SUBMIT): ServiceDeskTicketStatus.SUBMITTED,
    (
        ServiceDeskTicketStatus.SUBMITTED,
        ServiceDeskTicketAction.START_APPROVAL,
    ): ServiceDeskTicketStatus.PENDING_APPROVAL,
    (
        ServiceDeskTicketStatus.SUBMITTED,
        ServiceDeskTicketAction.SKIP_APPROVAL,
    ): ServiceDeskTicketStatus.APPROVED,
    (
        ServiceDeskTicketStatus.PENDING_APPROVAL,
        ServiceDeskTicketAction.COMPLETE_APPROVAL,
    ): ServiceDeskTicketStatus.APPROVED,
    (
        ServiceDeskTicketStatus.PENDING_APPROVAL,
        ServiceDeskTicketAction.REJECT_APPROVAL,
    ): ServiceDeskTicketStatus.REJECTED,
    (
        ServiceDeskTicketStatus.APPROVED,
        ServiceDeskTicketAction.ASSIGN,
    ): ServiceDeskTicketStatus.ASSIGNED,
    **{
        (ticket_status, ServiceDeskTicketAction.REASSIGN): ticket_status
        for ticket_status in REASSIGNABLE_STATUSES
    },
    (
        ServiceDeskTicketStatus.ASSIGNED,
        ServiceDeskTicketAction.START,
    ): ServiceDeskTicketStatus.IN_PROGRESS,
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.REQUEST_CLARIFICATION,
    ): ServiceDeskTicketStatus.WAITING_REQUESTER,
    (
        ServiceDeskTicketStatus.WAITING_REQUESTER,
        ServiceDeskTicketAction.REQUESTER_REPLY,
    ): ServiceDeskTicketStatus.IN_PROGRESS,
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.WAIT_EXTERNAL,
    ): ServiceDeskTicketStatus.WAITING_EXTERNAL,
    (
        ServiceDeskTicketStatus.WAITING_EXTERNAL,
        ServiceDeskTicketAction.RESUME,
    ): ServiceDeskTicketStatus.IN_PROGRESS,
    (
        ServiceDeskTicketStatus.IN_PROGRESS,
        ServiceDeskTicketAction.RESOLVE,
    ): ServiceDeskTicketStatus.RESOLVED,
    (
        ServiceDeskTicketStatus.RESOLVED,
        ServiceDeskTicketAction.CLOSE,
    ): ServiceDeskTicketStatus.CLOSED,
}

CANCELLABLE_STATUSES = {
    ServiceDeskTicketStatus.DRAFT,
    ServiceDeskTicketStatus.SUBMITTED,
    ServiceDeskTicketStatus.PENDING_APPROVAL,
    ServiceDeskTicketStatus.APPROVED,
    ServiceDeskTicketStatus.ASSIGNED,
    ServiceDeskTicketStatus.IN_PROGRESS,
    ServiceDeskTicketStatus.WAITING_REQUESTER,
    ServiceDeskTicketStatus.WAITING_EXTERNAL,
}

REQUESTER_CANCELLABLE_STATUSES = {
    ServiceDeskTicketStatus.DRAFT,
    ServiceDeskTicketStatus.SUBMITTED,
    ServiceDeskTicketStatus.PENDING_APPROVAL,
}

SYSTEM_ACTIONS = {
    ServiceDeskTicketAction.START_APPROVAL,
    ServiceDeskTicketAction.SKIP_APPROVAL,
    ServiceDeskTicketAction.COMPLETE_APPROVAL,
    ServiceDeskTicketAction.ASSIGN,
}

ASSIGNMENT_ACTIONS = {
    ServiceDeskTicketAction.ASSIGN,
    ServiceDeskTicketAction.REASSIGN,
}

ASSIGNEE_ACTIONS = {
    ServiceDeskTicketAction.START,
    ServiceDeskTicketAction.REQUEST_CLARIFICATION,
    ServiceDeskTicketAction.WAIT_EXTERNAL,
    ServiceDeskTicketAction.RESUME,
    ServiceDeskTicketAction.RESOLVE,
}

ACTION_EVENTS = {
    ServiceDeskTicketAction.SUBMIT: ("ticket_submitted", "Заявка отправлена"),
    ServiceDeskTicketAction.START_APPROVAL: ("approval_started", "Заявка направлена на согласование"),
    ServiceDeskTicketAction.SKIP_APPROVAL: ("ticket_approved", "Согласование для заявки не требуется"),
    ServiceDeskTicketAction.COMPLETE_APPROVAL: ("ticket_approved", "Согласование заявки завершено"),
    ServiceDeskTicketAction.REJECT_APPROVAL: ("ticket_rejected", "Заявка отклонена"),
    ServiceDeskTicketAction.ASSIGN: ("ticket_assigned", "Исполнитель назначен"),
    ServiceDeskTicketAction.REASSIGN: ("ticket_reassigned", "Исполнитель переназначен"),
    ServiceDeskTicketAction.START: ("ticket_started", "Заявка взята в работу"),
    ServiceDeskTicketAction.REQUEST_CLARIFICATION: (
        "clarification_requested",
        "Запрошено уточнение у заявителя",
    ),
    ServiceDeskTicketAction.REQUESTER_REPLY: ("requester_replied", "Заявитель предоставил уточнение"),
    ServiceDeskTicketAction.WAIT_EXTERNAL: (
        "ticket_waiting_external",
        "Заявка ожидает внешнего действия",
    ),
    ServiceDeskTicketAction.RESUME: ("ticket_resumed", "Работа по заявке продолжена"),
    ServiceDeskTicketAction.RESOLVE: ("ticket_resolved", "По заявке зафиксировано решение"),
    ServiceDeskTicketAction.CLOSE: ("ticket_closed", "Заявка закрыта"),
    ServiceDeskTicketAction.CANCEL: ("ticket_cancelled", "Заявка отменена"),
}


def transition_target(
    current_status: ServiceDeskTicketStatus,
    action: ServiceDeskTicketAction,
) -> ServiceDeskTicketStatus | None:
    if action == ServiceDeskTicketAction.CANCEL and current_status in CANCELLABLE_STATUSES:
        return ServiceDeskTicketStatus.CANCELLED
    return TRANSITION_TARGETS.get((current_status, action))


class TicketLifecycleService:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    def perform_transition(
        self,
        ticket: ServiceDeskTicket,
        action: ServiceDeskTicketAction,
        *,
        actor: ServiceDeskUser | None,
        metadata: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ServiceDeskTicket:
        target_status = transition_target(ticket.status, action)
        if target_status is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Действие {action.value} недоступно для статуса {ticket.status.value}",
            )

        payload = {key: value for key, value in (metadata or {}).items() if value is not None}
        self._authorize(ticket, action, actor)
        self._validate_payload(action, payload)

        previous_status = ticket.status
        now = occurred_at or datetime.now(UTC)
        ticket.status = target_status
        self._apply_action_data(ticket, action, payload, now)

        event_type, message = ACTION_EVENTS[action]
        self.repository.add_history(
            ServiceDeskTicketHistory(
                ticket_id=ticket.id,
                event_type=event_type,
                actor_user_id=actor.id if actor else None,
                message=message,
                payload={
                    "from_status": previous_status.value,
                    "to_status": target_status.value,
                    **payload,
                },
            )
        )
        return ticket

    @staticmethod
    def _authorize(
        ticket: ServiceDeskTicket,
        action: ServiceDeskTicketAction,
        actor: ServiceDeskUser | None,
    ) -> None:
        if actor is None:
            if action in SYSTEM_ACTIONS:
                return
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Для действия требуется пользователь")
        if not actor.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")

        is_admin = actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
        if action in ASSIGNMENT_ACTIONS:
            can_assign = is_admin or any(
                capability.capability == "service_desk.assign" for capability in actor.capabilities
            )
            if not can_assign:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет capability service_desk.assign")
            return
        if action == ServiceDeskTicketAction.SUBMIT:
            if actor.id != ticket.requester_user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Отправить заявку может только заявитель")
            return
        if action in ASSIGNEE_ACTIONS:
            if actor.id != ticket.assignee_user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Действие доступно только исполнителю")
            return
        if action == ServiceDeskTicketAction.REQUESTER_REPLY:
            if actor.id != ticket.requester_user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Ответить может только заявитель")
            return
        if action == ServiceDeskTicketAction.CLOSE:
            if not is_admin and actor.id not in {ticket.requester_user_id, ticket.assignee_user_id}:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для закрытия заявки")
            return
        if action == ServiceDeskTicketAction.CANCEL:
            requester_can_cancel = (
                actor.id == ticket.requester_user_id
                and ticket.status in REQUESTER_CANCELLABLE_STATUSES
            )
            if not is_admin and not requester_can_cancel:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для отмены заявки")

    @staticmethod
    def _validate_payload(action: ServiceDeskTicketAction, payload: dict[str, Any]) -> None:
        required_fields = {
            ServiceDeskTicketAction.REQUEST_CLARIFICATION: "comment",
            ServiceDeskTicketAction.WAIT_EXTERNAL: "reason",
            ServiceDeskTicketAction.RESOLVE: "resolution_summary",
            ServiceDeskTicketAction.REJECT_APPROVAL: "comment",
            ServiceDeskTicketAction.CANCEL: "reason",
            ServiceDeskTicketAction.ASSIGN: "assignee_user_id",
            ServiceDeskTicketAction.REASSIGN: "assignee_user_id",
        }
        field = required_fields.get(action)
        if field and (not isinstance(payload.get(field), str) or not payload[field].strip()):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Для действия {action.value} требуется поле {field}",
            )

    @staticmethod
    def _apply_action_data(
        ticket: ServiceDeskTicket,
        action: ServiceDeskTicketAction,
        payload: dict[str, Any],
        now: datetime,
    ) -> None:
        timestamp_fields = {
            ServiceDeskTicketAction.SUBMIT: "submitted_at",
            ServiceDeskTicketAction.START_APPROVAL: "approval_started_at",
            ServiceDeskTicketAction.SKIP_APPROVAL: "approved_at",
            ServiceDeskTicketAction.COMPLETE_APPROVAL: "approved_at",
            ServiceDeskTicketAction.REJECT_APPROVAL: "rejected_at",
            ServiceDeskTicketAction.ASSIGN: "assigned_at",
            ServiceDeskTicketAction.REASSIGN: "assigned_at",
            ServiceDeskTicketAction.START: "work_started_at",
            ServiceDeskTicketAction.RESOLVE: "resolved_at",
            ServiceDeskTicketAction.CLOSE: "closed_at",
            ServiceDeskTicketAction.CANCEL: "cancelled_at",
        }
        timestamp_field = timestamp_fields.get(action)
        if timestamp_field:
            setattr(ticket, timestamp_field, now)
        if action == ServiceDeskTicketAction.RESOLVE:
            ticket.resolution_summary = payload["resolution_summary"].strip()
        if action == ServiceDeskTicketAction.CANCEL:
            ticket.cancellation_reason = payload["reason"].strip()
        if action in ASSIGNMENT_ACTIONS:
            ticket.assignee_user_id = uuid.UUID(str(payload["assignee_user_id"]))
