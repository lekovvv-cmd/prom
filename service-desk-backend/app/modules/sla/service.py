from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.access.models import ServiceDeskUser
from app.modules.sla import schemas
from app.modules.sla.models import ServiceDeskBusinessCalendar, ServiceDeskBusinessHours
from app.modules.sla.repository import SlaRepository


class SlaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SlaRepository(db)

    def list_calendars(self, actor: ServiceDeskUser) -> list[ServiceDeskBusinessCalendar]:
        self._require_manage_sla(actor)
        return self.repository.list_calendars()

    def create_calendar(
        self,
        payload: schemas.BusinessCalendarCreate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskBusinessCalendar:
        self._require_manage_sla(actor)
        self._validate_business_hours(payload.business_hours)
        calendar = self.repository.add_calendar(
            ServiceDeskBusinessCalendar(
                name=payload.name.strip(),
                timezone=payload.timezone,
                is_active=payload.is_active,
                business_hours=self._business_hours(payload.business_hours),
            )
        )
        self.db.commit()
        return self._require_calendar(calendar.id)

    def update_calendar(
        self,
        calendar_id: uuid.UUID,
        payload: schemas.BusinessCalendarUpdate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskBusinessCalendar:
        self._require_manage_sla(actor)
        calendar = self._require_calendar(calendar_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            calendar.name = payload.name.strip() if payload.name else calendar.name
        if "timezone" in data:
            calendar.timezone = payload.timezone
        if "is_active" in data:
            calendar.is_active = payload.is_active
        if "business_hours" in data:
            self._validate_business_hours(payload.business_hours or [])
            calendar.business_hours = self._business_hours(payload.business_hours or [])
        self.db.commit()
        return self._require_calendar(calendar.id)

    @staticmethod
    def _business_hours(
        intervals: list[schemas.BusinessHoursInput],
    ) -> list[ServiceDeskBusinessHours]:
        return [
            ServiceDeskBusinessHours(
                weekday=interval.weekday,
                start_time=interval.start_time,
                end_time=interval.end_time,
            )
            for interval in intervals
        ]

    @staticmethod
    def _validate_business_hours(intervals: list[schemas.BusinessHoursInput]) -> None:
        by_weekday: dict[int, list[schemas.BusinessHoursInput]] = defaultdict(list)
        for interval in intervals:
            by_weekday[interval.weekday].append(interval)
        for weekday_intervals in by_weekday.values():
            ordered = sorted(weekday_intervals, key=lambda interval: interval.start_time)
            if any(
                current.end_time > following.start_time
                for current, following in zip(ordered, ordered[1:], strict=False)
            ):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Business hour intervals for one weekday must not overlap",
                )

    def _require_calendar(self, calendar_id: uuid.UUID) -> ServiceDeskBusinessCalendar:
        calendar = self.repository.get_calendar(calendar_id)
        if not calendar:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Business calendar not found")
        return calendar

    @staticmethod
    def _require_manage_sla(actor: ServiceDeskUser) -> None:
        if any(item.capability == "service_desk.manage_sla" for item in actor.capabilities):
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing service_desk.manage_sla capability")
