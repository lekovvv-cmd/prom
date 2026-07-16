import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ServiceDeskCommentVisibility
from app.modules.tickets.schemas import TicketUserSummary


class TicketCommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=5000)
    visibility: ServiceDeskCommentVisibility = ServiceDeskCommentVisibility.PUBLIC


class TicketCommentUpdate(BaseModel):
    body: str = Field(min_length=2, max_length=5000)


class TicketCommentRead(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_user_id: uuid.UUID
    author: TicketUserSummary
    body: str
    visibility: ServiceDeskCommentVisibility
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
