import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_user_id: uuid.UUID
    ticket_id: uuid.UUID | None
    event_type: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None


class UnreadCount(BaseModel):
    count: int


class ReadAllResult(BaseModel):
    marked_read: int
