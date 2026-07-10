import uuid
from datetime import date, datetime, time
from enum import StrEnum
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BusinessHoursInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_interval(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        return self


class BusinessHoursRead(BusinessHoursInput):
    id: uuid.UUID
    calendar_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class CalendarExceptionType(StrEnum):
    HOLIDAY = "holiday"
    WORKING_DAY = "working_day"
    CUSTOM_HOURS = "custom_hours"


class CalendarExceptionInput(BaseModel):
    date: date
    type: CalendarExceptionType
    start_time: time | None = None
    end_time: time | None = None
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_times(self):
        if self.type == CalendarExceptionType.CUSTOM_HOURS:
            if self.start_time is None or self.end_time is None:
                raise ValueError("custom_hours requires start_time and end_time")
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be later than start_time")
        elif self.start_time is not None or self.end_time is not None:
            raise ValueError("start_time and end_time are only allowed for custom_hours")
        return self


class CalendarExceptionRead(CalendarExceptionInput):
    id: uuid.UUID
    calendar_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BusinessCalendarCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    timezone: str = Field(min_length=1, max_length=64)
    is_active: bool = True
    business_hours: list[BusinessHoursInput] = Field(min_length=1)
    exceptions: list[CalendarExceptionInput] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be an IANA timezone") from exc
        return value


class BusinessCalendarUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None
    business_hours: list[BusinessHoursInput] | None = Field(default=None, min_length=1)
    exceptions: list[CalendarExceptionInput] | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be an IANA timezone") from exc
        return value


class BusinessCalendarRead(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str
    is_active: bool
    business_hours: list[BusinessHoursRead]
    exceptions: list[CalendarExceptionRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlaPolicyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True
    business_calendar_id: uuid.UUID
    first_response_minutes: int = Field(gt=0)
    resolution_minutes: int = Field(gt=0)
    pause_statuses: list[Literal["waiting_requester", "waiting_external"]] = Field(default_factory=list)


class SlaPolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    business_calendar_id: uuid.UUID | None = None
    first_response_minutes: int | None = Field(default=None, gt=0)
    resolution_minutes: int | None = Field(default=None, gt=0)
    pause_statuses: list[Literal["waiting_requester", "waiting_external"]] | None = None


class SlaPolicyRead(SlaPolicyCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SlaBindingCondition(BaseModel):
    field: Literal["template_version_id", "service_id", "category_id", "priority", "field_value"]
    value: Any
    field_key: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_field_key(self):
        if self.field == "field_value" and not self.field_key:
            raise ValueError("field_value requires field_key")
        if self.field != "field_value" and self.field_key is not None:
            raise ValueError("field_key is only allowed for field_value")
        return self


class SlaBindingCreate(BaseModel):
    policy_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    priority: int = Field(default=100, ge=0, le=1_000_000)
    is_active: bool = True
    conditions: list[SlaBindingCondition] = Field(min_length=1)


class SlaBindingUpdate(BaseModel):
    policy_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    priority: int | None = Field(default=None, ge=0, le=1_000_000)
    is_active: bool | None = None
    conditions: list[SlaBindingCondition] | None = Field(default=None, min_length=1)


class SlaBindingRead(SlaBindingCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationRuleCreate(BaseModel):
    metric: Literal["first_response", "resolution"]
    threshold_percent: int = Field(gt=0)
    action_type: Literal["create_in_app_notification", "email_notification_when_available"]
    recipient_type: Literal["assignee", "requester", "service_desk_admin", "specific_user"]
    recipient_user_id: uuid.UUID | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_recipient(self):
        if (self.recipient_type == "specific_user") != (self.recipient_user_id is not None):
            raise ValueError("recipient_user_id is required only for specific_user")
        return self


class EscalationRuleUpdate(BaseModel):
    metric: Literal["first_response", "resolution"] | None = None
    threshold_percent: int | None = Field(default=None, gt=0)
    action_type: Literal["create_in_app_notification", "email_notification_when_available"] | None = None
    recipient_type: Literal["assignee", "requester", "service_desk_admin", "specific_user"] | None = None
    recipient_user_id: uuid.UUID | None = None
    is_active: bool | None = None


class EscalationRuleRead(EscalationRuleCreate):
    id: uuid.UUID
    sla_policy_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
