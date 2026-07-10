from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskTicketStatus
from app.modules.sla.models import ServiceDeskTicketSlaPause
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
        self.db.commit()
        return counts

    def _history(self, ticket: ServiceDeskTicket, metric: str, occurred_at: datetime) -> None:
        self.db.add(ServiceDeskTicketHistory(
            ticket_id=ticket.id,
            event_type="sla_breached",
            actor_user_id=None,
            message="SLA deadline breached",
            payload={"metric": metric, "due_at": getattr(ticket, f"{metric}_due_at").isoformat()},
            created_at=occurred_at,
        ))
