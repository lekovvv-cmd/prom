import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus


class WorkbenchSlaState(StrEnum):
    NO_SLA = "no_sla"
    ON_TRACK = "on_track"
    PAUSED = "paused"
    WARNING = "warning"
    BREACHED = "breached"


class WorkbenchEntitySummary(BaseModel):
    id: uuid.UUID
    title: str


class WorkbenchUserSummary(BaseModel):
    id: uuid.UUID
    display_name: str


class WorkbenchSlaSummary(BaseModel):
    state: WorkbenchSlaState
    metric: str | None = None
    due_at: datetime | None = None


class WorkbenchTicketRow(BaseModel):
    ticket_id: uuid.UUID
    number: str | None
    title: str
    service: WorkbenchEntitySummary
    category: WorkbenchEntitySummary
    requester: WorkbenchUserSummary
    assignee: WorkbenchUserSummary | None
    priority: ServiceDeskPriority
    status: ServiceDeskTicketStatus
    sla: WorkbenchSlaSummary
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str] = Field(default_factory=list)


class WorkbenchTicketPage(BaseModel):
    items: list[WorkbenchTicketRow]
    page: int
    page_size: int
    total: int
    pages: int
