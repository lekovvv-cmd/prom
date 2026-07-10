from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class NotificationEventType(StrEnum):
    TICKET_SUBMITTED = "ticket_submitted"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_REASSIGNED = "ticket_reassigned"
    TICKET_STARTED = "ticket_started"
    CLARIFICATION_REQUESTED = "clarification_requested"
    REQUESTER_REPLIED = "requester_replied"
    TICKET_WAITING_EXTERNAL = "ticket_waiting_external"
    SLA_WARNING = "sla_warning"
    SLA_BREACHED = "sla_breached"
    TICKET_RESOLVED = "ticket_resolved"
    TICKET_CLOSED = "ticket_closed"
    TICKET_CANCELLED = "ticket_cancelled"


@dataclass(frozen=True)
class NotificationEvent:
    event_type: NotificationEventType
    ticket_id: uuid.UUID | None
    title: str
    body: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    recipient_user_ids: tuple[uuid.UUID, ...] | None = None
