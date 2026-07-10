from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.access.models import ServiceDeskUser
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.notifications.domain import NotificationEvent, NotificationEventType
from app.modules.notifications.models import ServiceDeskNotification
from app.modules.notifications.repository import NotificationRepository
from app.modules.tickets.models import ServiceDeskTicket


class InAppChannel:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    def deliver(self, event: NotificationEvent, recipient_user_id: uuid.UUID) -> None:
        if self.repository.exists(event.event_id, recipient_user_id):
            return
        self.repository.add(
            ServiceDeskNotification(
                event_id=event.event_id,
                recipient_user_id=recipient_user_id,
                ticket_id=event.ticket_id,
                event_type=event.event_type.value,
                title=event.title,
                body=event.body,
            )
        )


class NotificationDispatcher:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.in_app = InAppChannel(NotificationRepository(db))

    def dispatch(self, event: NotificationEvent) -> None:
        for recipient_id in self._recipient_ids(event):
            self.in_app.deliver(event, recipient_id)

    def _recipient_ids(self, event: NotificationEvent) -> list[uuid.UUID]:
        if event.recipient_user_ids is not None:
            candidates = set(event.recipient_user_ids)
        elif event.ticket_id is None:
            candidates = set()
        else:
            ticket = self.db.get(ServiceDeskTicket, event.ticket_id)
            if ticket is None:
                return []
            requester_events = {
                NotificationEventType.TICKET_SUBMITTED,
                NotificationEventType.APPROVAL_APPROVED,
                NotificationEventType.APPROVAL_REJECTED,
                NotificationEventType.TICKET_STARTED,
                NotificationEventType.CLARIFICATION_REQUESTED,
                NotificationEventType.TICKET_WAITING_EXTERNAL,
                NotificationEventType.TICKET_RESOLVED,
                NotificationEventType.TICKET_CLOSED,
                NotificationEventType.TICKET_CANCELLED,
            }
            assignee_events = {
                NotificationEventType.TICKET_ASSIGNED,
                NotificationEventType.TICKET_REASSIGNED,
                NotificationEventType.REQUESTER_REPLIED,
                NotificationEventType.SLA_WARNING,
                NotificationEventType.SLA_BREACHED,
            }
            candidates = set()
            if event.event_type in requester_events:
                candidates.add(ticket.requester_user_id)
            if event.event_type in assignee_events and ticket.assignee_user_id:
                candidates.add(ticket.assignee_user_id)
            if event.event_type == NotificationEventType.APPROVAL_REQUESTED:
                candidates.update(self._pending_approvers(ticket.id))
            if event.event_type in {NotificationEventType.SLA_WARNING, NotificationEventType.SLA_BREACHED}:
                candidates.add(ticket.requester_user_id)
        active_ids = set(
            self.db.scalars(
                select(ServiceDeskUser.id).where(
                    ServiceDeskUser.id.in_(candidates), ServiceDeskUser.is_active.is_(True)
                )
            ).all()
        ) if candidates else set()
        return sorted(active_ids, key=str)

    def _pending_approvers(self, ticket_id: uuid.UUID) -> list[uuid.UUID]:
        return list(self.db.scalars(
            select(ServiceDeskTicketApproval.approver_user_id)
            .join(ServiceDeskTicketApprovalStage)
            .where(
                ServiceDeskTicketApprovalStage.ticket_id == ticket_id,
                ServiceDeskTicketApprovalStage.started_at.is_not(None),
                ServiceDeskTicketApproval.status == "pending",
            )
        ).all())


EVENT_COPY: dict[NotificationEventType, tuple[str, str]] = {
    NotificationEventType.TICKET_SUBMITTED: ("Заявка отправлена", "Заявка зарегистрирована в Service Desk."),
    NotificationEventType.APPROVAL_REQUESTED: ("Требуется согласование", "Заявка ожидает вашего решения."),
    NotificationEventType.APPROVAL_APPROVED: ("Заявка согласована", "Согласование заявки одобрено."),
    NotificationEventType.APPROVAL_REJECTED: ("Заявка отклонена", "Согласующий отклонил заявку."),
    NotificationEventType.TICKET_ASSIGNED: ("Назначена заявка", "Вы назначены исполнителем заявки."),
    NotificationEventType.TICKET_REASSIGNED: ("Заявка переназначена", "Заявка назначена вам как новому исполнителю."),
    NotificationEventType.TICKET_STARTED: ("Заявка в работе", "Исполнитель начал работу по заявке."),
    NotificationEventType.CLARIFICATION_REQUESTED: ("Нужно уточнение", "Исполнитель ожидает вашего ответа."),
    NotificationEventType.REQUESTER_REPLIED: ("Получен ответ заявителя", "Заявитель предоставил уточнение."),
    NotificationEventType.TICKET_WAITING_EXTERNAL: ("Ожидается внешнее действие", "Работа по заявке временно ожидает внешнего действия."),
    NotificationEventType.SLA_WARNING: ("Приближается срок SLA", "Срок обработки заявки скоро будет нарушен."),
    NotificationEventType.SLA_BREACHED: ("SLA нарушен", "Срок обработки заявки нарушен."),
    NotificationEventType.TICKET_RESOLVED: ("Заявка выполнена", "По заявке зафиксировано решение."),
    NotificationEventType.TICKET_CLOSED: ("Заявка закрыта", "Работа по заявке завершена."),
    NotificationEventType.TICKET_CANCELLED: ("Заявка отменена", "Заявка была отменена."),
}


def ticket_notification(event_type: NotificationEventType, ticket_id: uuid.UUID, *, recipient_user_ids=None) -> NotificationEvent:
    title, body = EVENT_COPY[event_type]
    return NotificationEvent(event_type, ticket_id, title, body, recipient_user_ids=recipient_user_ids)
