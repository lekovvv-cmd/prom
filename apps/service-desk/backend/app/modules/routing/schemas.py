import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import ServiceDeskPriority
from app.modules.catalog.schemas import CategoryRead, ServiceRead


class RoutingCondition(BaseModel):
    field: Literal["service_id", "category_id", "priority", "field_value"]
    operator: Literal["equals"]
    value: Any
    field_key: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_field_key(self):
        if self.field == "field_value" and not self.field_key:
            raise ValueError("Для field_value требуется field_key")
        if self.field != "field_value" and self.field_key is not None:
            raise ValueError("field_key поддерживается только для field_value")
        return self


class RoutingAction(BaseModel):
    type: Literal["assign_user", "set_priority"]
    user_id: uuid.UUID | None = None
    priority: ServiceDeskPriority | None = None

    @model_validator(mode="after")
    def validate_action_payload(self):
        if self.type == "assign_user" and self.user_id is None:
            raise ValueError("Для assign_user требуется user_id")
        if self.type == "set_priority" and self.priority is None:
            raise ValueError("Для set_priority требуется priority")
        if self.type != "assign_user" and self.user_id is not None:
            raise ValueError("user_id поддерживается только для assign_user")
        if self.type != "set_priority" and self.priority is not None:
            raise ValueError("priority поддерживается только для set_priority")
        return self


class RoutingRuleDefinition(BaseModel):
    conditions: list[RoutingCondition] = Field(default_factory=list)
    action: RoutingAction


class RoutingRuleCreate(RoutingRuleDefinition):
    name: str = Field(min_length=2, max_length=255)
    priority: int = Field(default=100, ge=0, le=1_000_000)
    is_active: bool = True


class RoutingRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    priority: int | None = Field(default=None, ge=0, le=1_000_000)
    is_active: bool | None = None
    conditions: list[RoutingCondition] | None = None
    action: RoutingAction | None = None


class RoutingRuleRead(RoutingRuleDefinition):
    id: uuid.UUID
    name: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoutingRulesReorder(BaseModel):
    rule_ids: list[uuid.UUID] = Field(min_length=1)


class RoutingAssigneeRead(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class RoutingCatalogOptionsRead(BaseModel):
    """Catalog entities available as routing rule conditions."""

    categories: list[CategoryRead]
    services: list[ServiceRead]
