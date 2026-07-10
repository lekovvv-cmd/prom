from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskTicketStatus
from app.modules.sla.engine import add_business_minutes
from app.modules.sla.models import (
    ServiceDeskEscalationRule,
    ServiceDeskSlaEscalationEvent,
    ServiceDeskTicketSlaPause,
)
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


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class SlaWorker:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_once(self, *, now: datetime | None = None) -> dict[str, int]:
        occurred_at = now or datetime.now(UTC)
        active_pause = exists().where(
            ServiceDeskTicketSlaPause.ticket_id == ServiceDeskTicket.id,
            ServiceDeskTicketSlaPause.ended_at.is_(None),
        )
        tickets = self.db.scalars(
            select(ServiceDeskTicket)
            .where(
                ServiceDeskTicket.sla_snapshot.is_not(None),
                ServiceDeskTicket.status.in_(ACTIVE_STATUSES),
                ~active_pause,
            )
            .with_for_update(skip_locked=True)
        ).all()
        counts = {"processed": len(tickets), "response_breaches": 0, "resolution_breaches": 0}
        for ticket in tickets:
            if (
                ticket.first_response_at is None
                and not ticket.is_response_breached
                and ticket.first_response_due_at
                and _utc(ticket.first_response_due_at) <= _utc(occurred_at)
            ):
                ticket.is_response_breached = True
                ticket.response_breached_at = occurred_at
                self._history(ticket, "first_response", occurred_at)
                counts["response_breaches"] += 1
            if (
                ticket.resolved_at is None
                and not ticket.is_resolution_breached
                and ticket.resolution_due_at
                and _utc(ticket.resolution_due_at) <= _utc(occurred_at)
            ):
                ticket.is_resolution_breached = True
                ticket.resolution_breached_at = occurred_at
                self._history(ticket, "resolution", occurred_at)
                counts["resolution_breaches"] += 1
            self._evaluate_escalations(ticket, occurred_at)
        self.db.commit()
        return counts

    def _evaluate_escalations(self, ticket: ServiceDeskTicket, occurred_at: datetime) -> None:
        rules = self.db.scalars(select(ServiceDeskEscalationRule).where(
            ServiceDeskEscalationRule.sla_policy_id == ticket.sla_policy_id,
            ServiceDeskEscalationRule.is_active.is_(True),
        )).all()
        existing = set(self.db.scalars(select(ServiceDeskSlaEscalationEvent.rule_id).where(
            ServiceDeskSlaEscalationEvent.ticket_id == ticket.id
        )).all())
        selected_at = datetime.fromisoformat(ticket.sla_snapshot["selected_at"])
        for rule in rules:
            if rule.id in existing:
                continue
            if rule.metric == "first_response" and ticket.first_response_at is not None:
                continue
            if rule.metric == "resolution" and ticket.resolved_at is not None:
                continue
            minutes = ticket.sla_snapshot[f"{rule.metric}_minutes"]
            threshold = add_business_minutes(
                selected_at, max(1, round(minutes * rule.threshold_percent / 100)), ticket.sla_snapshot
            )
            if threshold > _utc(occurred_at):
                continue
            recipient_user_id = (
                rule.recipient_user_id if rule.recipient_type == "specific_user"
                else ticket.assignee_user_id if rule.recipient_type == "assignee"
                else ticket.requester_user_id if rule.recipient_type == "requester" else None
            )
            self.db.add(ServiceDeskSlaEscalationEvent(
                ticket_id=ticket.id, rule_id=rule.id, metric=rule.metric,
                action_type=rule.action_type, recipient_type=rule.recipient_type,
                recipient_user_id=recipient_user_id,
            ))
            self.db.add(ServiceDeskTicketHistory(
                ticket_id=ticket.id, event_type="sla_warning" if rule.threshold_percent < 100 else "sla_escalated",
                actor_user_id=None, message="SLA escalation threshold reached",
                payload={"metric": rule.metric, "threshold_percent": rule.threshold_percent, "rule_id": str(rule.id)},
            ))

    def _history(self, ticket: ServiceDeskTicket, metric: str, occurred_at: datetime) -> None:
        self.db.add(ServiceDeskTicketHistory(
            ticket_id=ticket.id,
            event_type="sla_breached",
            actor_user_id=None,
            message="SLA deadline breached",
            payload={"metric": metric, "due_at": getattr(ticket, f"{metric}_due_at").isoformat()},
            created_at=occurred_at,
        ))
