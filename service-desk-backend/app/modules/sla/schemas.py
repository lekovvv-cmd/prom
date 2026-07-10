import uuid
from datetime import date, datetime, time
from enum import StrEnum
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
