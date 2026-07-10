import uuid
from datetime import datetime, time
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


class BusinessCalendarCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    timezone: str = Field(min_length=1, max_length=64)
    is_active: bool = True
    business_hours: list[BusinessHoursInput] = Field(min_length=1)

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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
