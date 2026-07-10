import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.enums import ServiceDeskAccessType


class ServiceDeskUserRead(BaseModel):
    id: uuid.UUID
    identity_user_id: str
    email: str
    display_name: str
    department: str | None
    position: str | None
    access_type: ServiceDeskAccessType
    is_active: bool
    capabilities: list[str]
    created_at: datetime
    updated_at: datetime


class ServiceDeskCapabilitiesRead(BaseModel):
    capabilities: list[str]
