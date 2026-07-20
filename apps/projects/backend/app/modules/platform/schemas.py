from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProjectAuditEventRead(BaseModel):
    id: str
    actor_user_id: str | None
    external_user_id: str | None
    action: str
    module: str
    object_type: str
    object_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    request_id: str | None
    result: str
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
