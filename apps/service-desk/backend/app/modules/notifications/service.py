from __future__ import annotations

import uuid
from datetime import UTC, datetime

from platform_sdk.error_types import EntityNotFound
from platform_sdk.outbox import mark_outbox_processed
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.access.models import ServiceDeskUser
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.notifications.domain import (
    NotificationChannel,
    NotificationEvent,
    NotificationEventType,
)
from app.modules.notifications.models import ServiceDeskNotification, ServiceDeskNotificationOutbox
from app.modules.notifications.repository import (
    NotificationOutboxRepository,
    NotificationRepository,
)
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


class EmailChannel:
    """Persists email intent without pretending unavailable external delivery succeeded."""

    def __init__(self, repository: NotificationOutboxRepository) -> None:
        self.repository = repository

    def enqueue(self, event: NotificationEvent, recipient_email: str) -> None:
        self.repository.get_or_add(ServiceDeskNotificationOutbox(
            event_id=event.event_id,
            event_type=event.event_type.value,
            aggregate_type="service_desk_ticket",
            aggregate_id=str(event.ticket_id or event.event_id),
            channel="email",
            recipient=recipient_email,
            payload={
                "ticket_id": str(event.ticket_id) if event.ticket_id else None,
                "event_type": event.event_type.value,
                "title": event.title,
                "body": event.body,
            },
            status="blocked_external",
            last_error="Email delivery configuration has not been provided by CIT",
        ))


class NotificationDispatcher:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.in_app = InAppChannel(NotificationRepository(db))
        self.outbox = NotificationOutboxRepository(db)
        self.email = EmailChannel(self.outbox)

    def dispatch(self, event: NotificationEvent) -> None:
        for recipient_id in self._recipient_ids(event):
            if NotificationChannel.IN_APP in event.channels:
                record = self.outbox.get_or_add(ServiceDeskNotificationOutbox(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    aggregate_type="service_desk_ticket",
                    aggregate_id=str(event.ticket_id or event.event_id),
                    channel="in_app",
                    recipient=str(recipient_id),
                    payload=self._outbox_payload(event),
                    payload_version=1,
                    status="pending",
                ))
                if record.status != "processed":
                    self.in_app.deliver(event, recipient_id)
                    mark_outbox_processed(record, now=datetime.now(UTC))
            if NotificationChannel.EMAIL in event.channels:
                recipient = self.db.get(ServiceDeskUser, recipient_id)
                if recipient:
                    self.email.enqueue(event, recipient.email)

    @staticmethod
    def _outbox_payload(event: NotificationEvent) -> dict[str, str | None]:
        return {
            "ticket_id": str(event.ticket_id) if event.ticket_id else None,
            "event_type": event.event_type.value,
            "title": event.title,
            "body": event.body,
        }

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


def ticket_notification(
    event_type: NotificationEventType,
    ticket_id: uuid.UUID,
    *,
    recipient_user_ids=None,
    event_id: uuid.UUID | None = None,
    channels: frozenset[NotificationChannel] | None = None,
) -> NotificationEvent:
    title, body = EVENT_COPY[event_type]
    kwargs = {"event_id": event_id} if event_id is not None else {}
    return NotificationEvent(
        event_type,
        ticket_id,
        title,
        body,
        recipient_user_ids=recipient_user_ids,
        channels=channels if channels is not None else frozenset({NotificationChannel.IN_APP, NotificationChannel.EMAIL}),
        **kwargs,
    )


def sla_notification(
    event_type: NotificationEventType,
    ticket_id: uuid.UUID,
    *,
    metric: str,
    threshold_percent: int | None = None,
    recipient_user_ids=None,
    event_id: uuid.UUID | None = None,
    channels: frozenset[NotificationChannel] | None = None,
) -> NotificationEvent:
    metric_label = "первого ответа" if metric == "first_response" else "разрешения"
    if event_type == NotificationEventType.SLA_WARNING:
        threshold = f" достиг {threshold_percent}%" if threshold_percent is not None else " приближается к нарушению"
        title = f"SLA {metric_label}{threshold}"
        body = f"Срок {metric_label} по заявке требует внимания."
    else:
        title = f"SLA {metric_label} нарушен"
        body = f"Срок {metric_label} по заявке нарушен."
    return NotificationEvent(
        event_type, ticket_id, title, body,
        recipient_user_ids=recipient_user_ids,
        event_id=event_id or uuid.uuid4(),
        channels=channels if channels is not None else frozenset({NotificationChannel.IN_APP, NotificationChannel.EMAIL}),
    )


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = NotificationRepository(db)

    def list_current_user(self, actor: ServiceDeskUser, *, unread_only: bool = False, limit: int | None = None):
        requested_limit = limit if limit is not None else settings.notification_list_default_limit
        bounded_limit = min(max(1, requested_limit), settings.notification_list_max_limit)
        return self.repository.list_for_recipient(actor.id, unread_only=unread_only, limit=bounded_limit)

    def unread_count(self, actor: ServiceDeskUser) -> int:
        return self.repository.unread_count(actor.id)

    def mark_read(self, notification_id: uuid.UUID, actor: ServiceDeskUser):
        notification = self.repository.get_owned(notification_id, actor.id)
        if notification is None:
            raise EntityNotFound("Уведомление не найдено")
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def mark_all_read(self, actor: ServiceDeskUser) -> int:
        count = self.repository.mark_all_read(actor.id, datetime.now(UTC))
        self.db.commit()
        return count
