from __future__ import annotations

from datetime import UTC, datetime

from platform_sdk.observability import get_service_metrics
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAccessType, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.notifications.domain import NotificationChannel, NotificationEventType
from app.modules.notifications.service import NotificationDispatcher, sla_notification
from app.modules.sla.engine import (
    business_seconds_between,
    effective_business_seconds_between,
)
from app.modules.sla.models import (
    ServiceDeskEscalationRule,
    ServiceDeskSlaEscalationEvent,
    ServiceDeskTicketSlaPause,
)
from app.modules.sla.projection import utc as _utc
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory

ACTIVE_STATUSES = {
    ServiceDeskTicketStatus.SUBMITTED,
    ServiceDeskTicketStatus.PENDING_APPROVAL,
    ServiceDeskTicketStatus.APPROVED,
    ServiceDeskTicketStatus.ASSIGNED,
    ServiceDeskTicketStatus.IN_PROGRESS,
    ServiceDeskTicketStatus.WAITING_REQUESTER,
    ServiceDeskTicketStatus.WAITING_EXTERNAL,
}

class SlaWorker:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics = get_service_metrics(
            service="service-desk-sla-worker",
            module="service-desk",
        )

    def run_once(self, *, now: datetime | None = None) -> dict[str, int]:
        occurred_at = now or datetime.now(UTC)
        tickets = self.db.scalars(
            select(ServiceDeskTicket)
            .where(
                ServiceDeskTicket.sla_snapshot.is_not(None),
                ServiceDeskTicket.status.in_(ACTIVE_STATUSES),
            )
            .with_for_update(skip_locked=True)
        ).all()
        counts = {"processed": len(tickets), "response_breaches": 0, "resolution_breaches": 0}
        for ticket in tickets:
            resolution_paused = self._has_active_resolution_pause(ticket)
            if (
                ticket.first_response_at is None
                and not ticket.is_response_breached
                and ticket.first_response_due_at
                and _utc(ticket.first_response_due_at) <= _utc(occurred_at)
            ):
                ticket.is_response_breached = True
                ticket.response_breached_at = occurred_at
                self._history(ticket, "first_response", occurred_at)
                self._notify(ticket, NotificationEventType.SLA_BREACHED, "first_response")
                counts["response_breaches"] += 1
            if (
                ticket.resolved_at is None
                and not resolution_paused
                and not ticket.is_resolution_breached
                and ticket.resolution_due_at
                and _utc(ticket.resolution_due_at) <= _utc(occurred_at)
            ):
                ticket.is_resolution_breached = True
                ticket.resolution_breached_at = occurred_at
                self._history(ticket, "resolution", occurred_at)
                self._notify(ticket, NotificationEventType.SLA_BREACHED, "resolution")
                counts["resolution_breaches"] += 1
            self._evaluate_escalations(ticket, occurred_at)
        self.db.commit()
        return counts

    def _evaluate_escalations(self, ticket: ServiceDeskTicket, occurred_at: datetime) -> None:
        snapshot = ticket.sla_snapshot
        if snapshot is None:
            return
        rules = self.db.scalars(select(ServiceDeskEscalationRule).where(
            ServiceDeskEscalationRule.sla_policy_id == ticket.sla_policy_id,
            ServiceDeskEscalationRule.is_active.is_(True),
        )).all()
        existing = set(self.db.scalars(select(ServiceDeskSlaEscalationEvent.rule_id).where(
            ServiceDeskSlaEscalationEvent.ticket_id == ticket.id
        )).all())
        selected_at = _utc(datetime.fromisoformat(snapshot["selected_at"]))
        occurred_at = _utc(occurred_at)
        resolution_elapsed_seconds: int | None = None
        for rule in rules:
            if rule.id in existing:
                continue
            if rule.metric == "first_response" and ticket.first_response_at is not None:
                continue
            if rule.metric == "resolution" and ticket.resolved_at is not None:
                continue
            minutes = snapshot[f"{rule.metric}_minutes"]
            if rule.metric == "resolution":
                if resolution_elapsed_seconds is None:
                    resolution_elapsed_seconds = self._resolution_elapsed_seconds(
                        ticket,
                        snapshot,
                        selected_at,
                        occurred_at,
                    )
                elapsed_seconds = resolution_elapsed_seconds
            else:
                # Resolution pause statuses do not pause first-response SLA.
                elapsed_seconds = business_seconds_between(
                    selected_at,
                    occurred_at,
                    snapshot,
                )
            if elapsed_seconds * 100 < minutes * 60 * rule.threshold_percent:
                continue
            recipient_user_id = (
                rule.recipient_user_id if rule.recipient_type == "specific_user"
                else ticket.assignee_user_id if rule.recipient_type == "assignee"
                else ticket.requester_user_id if rule.recipient_type == "requester" else None
            )
            escalation_event = ServiceDeskSlaEscalationEvent(
                ticket_id=ticket.id, rule_id=rule.id, metric=rule.metric,
                action_type=rule.action_type, recipient_type=rule.recipient_type,
                recipient_user_id=recipient_user_id,
            )
            self.db.add(escalation_event)
            self.db.flush()
            self.db.add(ServiceDeskTicketHistory(
                ticket_id=ticket.id, event_type="sla_warning" if rule.threshold_percent < 100 else "sla_escalated",
                actor_user_id=None, message="SLA escalation threshold reached",
                payload={"metric": rule.metric, "threshold_percent": rule.threshold_percent, "rule_id": str(rule.id)},
            ))
            if rule.threshold_percent < 100:
                self.metrics.record_sla_warning(rule.metric)
            else:
                self.metrics.record_sla_breach(rule.metric)
            if rule.action_type in {"create_in_app_notification", "email_notification_when_available"}:
                recipient_ids = [recipient_user_id] if recipient_user_id else []
                if rule.recipient_type == "service_desk_admin":
                    recipient_ids = list(self.db.scalars(select(ServiceDeskUser.id).where(
                        ServiceDeskUser.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN,
                        ServiceDeskUser.is_active.is_(True),
                    )).all())
                channels = frozenset({
                    NotificationChannel.IN_APP if rule.action_type == "create_in_app_notification"
                    else NotificationChannel.EMAIL
                })
                NotificationDispatcher(self.db).dispatch(sla_notification(
                    NotificationEventType.SLA_WARNING if rule.threshold_percent < 100 else NotificationEventType.SLA_BREACHED,
                    ticket.id,
                    recipient_user_ids=tuple(recipient_ids),
                    event_id=escalation_event.id,
                    channels=channels,
                    metric=rule.metric,
                    threshold_percent=rule.threshold_percent,
                ))

    def _resolution_elapsed_seconds(
        self,
        ticket: ServiceDeskTicket,
        snapshot: dict[str, object],
        selected_at: datetime,
        occurred_at: datetime,
    ) -> int:
        pauses = self.db.scalars(
            select(ServiceDeskTicketSlaPause).where(
                ServiceDeskTicketSlaPause.ticket_id == ticket.id,
                ServiceDeskTicketSlaPause.started_at < occurred_at,
            )
        ).all()
        pause_intervals = [
            (
                max(selected_at, _utc(pause.started_at)),
                min(occurred_at, _utc(pause.ended_at) if pause.ended_at else occurred_at),
            )
            for pause in pauses
        ]
        return effective_business_seconds_between(
            selected_at,
            occurred_at,
            snapshot,
            pause_intervals,
        )

    def _has_active_resolution_pause(self, ticket: ServiceDeskTicket) -> bool:
        return self.db.scalar(
            select(ServiceDeskTicketSlaPause.id).where(
                ServiceDeskTicketSlaPause.ticket_id == ticket.id,
                ServiceDeskTicketSlaPause.ended_at.is_(None),
            )
        ) is not None

    def _history(self, ticket: ServiceDeskTicket, metric: str, occurred_at: datetime) -> None:
        self.metrics.record_sla_breach(metric)
        self.db.add(ServiceDeskTicketHistory(
            ticket_id=ticket.id,
            event_type="sla_breached",
            actor_user_id=None,
            message="SLA deadline breached",
            payload={"metric": metric, "due_at": getattr(ticket, f"{metric}_due_at").isoformat()},
            created_at=occurred_at,
        ))

    def _notify(self, ticket: ServiceDeskTicket, event_type: NotificationEventType, metric: str) -> None:
        NotificationDispatcher(self.db).dispatch(sla_notification(event_type, ticket.id, metric=metric))
