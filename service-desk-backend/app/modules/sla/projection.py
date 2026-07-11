from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from app.core.enums import ServiceDeskTicketStatus
from app.modules.tickets.models import ServiceDeskTicket


SlaMetric = Literal["first_response", "resolution"]

TERMINAL_SLA_STATUSES = frozenset({
    ServiceDeskTicketStatus.REJECTED,
    ServiceDeskTicketStatus.RESOLVED,
    ServiceDeskTicketStatus.CLOSED,
    ServiceDeskTicketStatus.CANCELLED,
})


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def active_sla_metric(ticket: ServiceDeskTicket) -> SlaMetric | None:
    if not ticket.sla_snapshot or ticket.status in TERMINAL_SLA_STATUSES:
        return None
    if ticket.first_response_at is None:
        return "first_response"
    if ticket.resolved_at is None:
        return "resolution"
    return None


def active_sla_due_at(ticket: ServiceDeskTicket) -> datetime | None:
    metric = active_sla_metric(ticket)
    if metric == "first_response":
        return ticket.first_response_due_at
    if metric == "resolution":
        return ticket.resolution_due_at
    return None


def has_durable_sla_breach(ticket: ServiceDeskTicket) -> bool:
    return bool(ticket.is_response_breached or ticket.is_resolution_breached)


def current_metric_deadline_reached(ticket: ServiceDeskTicket, now: datetime) -> bool:
    due_at = active_sla_due_at(ticket)
    return due_at is not None and utc(due_at) <= utc(now)
