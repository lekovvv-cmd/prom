from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import AttachmentOwnerType, AttachmentStatus


class AttachmentRead(BaseModel):
    id: UUID
    owner_type: AttachmentOwnerType
    owner_id: UUID
    file_name: str
    content_type: str | None
    content_type_detected: str | None = None
    size_bytes: int
    checksum: str | None = None
    status: AttachmentStatus = AttachmentStatus.AVAILABLE
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
