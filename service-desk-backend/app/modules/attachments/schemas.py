import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import ServiceDeskAttachmentOwnerType


class ServiceDeskAttachmentRead(BaseModel):
    id: uuid.UUID
    owner_type: ServiceDeskAttachmentOwnerType
    owner_id: uuid.UUID
    ticket_id: uuid.UUID
    file_name: str
    content_type: str | None
    size_bytes: int
    uploaded_by_user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
