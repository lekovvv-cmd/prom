import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import ServiceDeskAttachmentOwnerType, ServiceDeskAttachmentStatus


class ServiceDeskAttachmentRead(BaseModel):
    id: uuid.UUID
    owner_type: ServiceDeskAttachmentOwnerType
    owner_id: uuid.UUID
    ticket_id: uuid.UUID
    field_key: str | None
    file_name: str
    content_type: str | None
    content_type_detected: str | None
    size_bytes: int
    checksum: str | None
    status: ServiceDeskAttachmentStatus
    uploaded_by_user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
