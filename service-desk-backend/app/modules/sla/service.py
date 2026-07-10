from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.access.models import ServiceDeskUser
from app.modules.sla import schemas
from app.modules.sla.models import (
    ServiceDeskBusinessCalendar,
    ServiceDeskBusinessHours,
    ServiceDeskCalendarException,
    ServiceDeskSlaBinding,
    ServiceDeskSlaPolicy,
)
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
        self._validate_exceptions(payload.exceptions)
        calendar = self.repository.add_calendar(
            ServiceDeskBusinessCalendar(
                name=payload.name.strip(),
                timezone=payload.timezone,
                is_active=payload.is_active,
                business_hours=self._business_hours(payload.business_hours),
                exceptions=self._exceptions(payload.exceptions),
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
        if "exceptions" in data:
            self._validate_exceptions(payload.exceptions or [])
            calendar.exceptions = self._exceptions(payload.exceptions or [])
        self.db.commit()
        return self._require_calendar(calendar.id)

    def list_policies(self, actor: ServiceDeskUser):
        self._require_manage_sla(actor)
        return self.repository.list_policies()

    def create_policy(self, payload: schemas.SlaPolicyCreate, actor: ServiceDeskUser):
        self._require_manage_sla(actor)
        self._require_calendar(payload.business_calendar_id)
        policy = self.repository.add_policy(ServiceDeskSlaPolicy(**payload.model_dump()))
        self.db.commit()
        return policy

    def update_policy(
        self, policy_id: uuid.UUID, payload: schemas.SlaPolicyUpdate, actor: ServiceDeskUser
    ):
        self._require_manage_sla(actor)
        policy = self._require_policy(policy_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("business_calendar_id"):
            self._require_calendar(data["business_calendar_id"])
        for field, value in data.items():
            setattr(policy, field, value.strip() if field == "name" else value)
        self.db.commit()
        return policy

    def list_bindings(self, actor: ServiceDeskUser):
        self._require_manage_sla(actor)
        return self.repository.list_bindings()

    def create_binding(self, payload: schemas.SlaBindingCreate, actor: ServiceDeskUser):
        self._require_manage_sla(actor)
        self._require_policy(payload.policy_id)
        binding = self.repository.add_binding(ServiceDeskSlaBinding(**payload.model_dump()))
        self.db.commit()
        return binding

    def update_binding(
        self, binding_id: uuid.UUID, payload: schemas.SlaBindingUpdate, actor: ServiceDeskUser
    ):
        self._require_manage_sla(actor)
        binding = self._require_binding(binding_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("policy_id"):
            self._require_policy(data["policy_id"])
        for field, value in data.items():
            setattr(binding, field, value.strip() if field == "name" else value)
        self.db.commit()
        return binding

    def snapshot_ticket(self, ticket, service, *, occurred_at) -> None:
        for binding in self.repository.list_bindings(active_only=True):
            policy = binding.policy
            if (
                policy.is_active
                and policy.deleted_at is None
                and self._matches(binding, ticket, service)
            ):
                calendar = self._require_calendar(policy.business_calendar_id)
                ticket.sla_snapshot = {
                    "binding_id": str(binding.id),
                    "binding_name": binding.name,
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "business_calendar_id": str(calendar.id),
                    "business_calendar_name": calendar.name,
                    "business_calendar_timezone": calendar.timezone,
                    "first_response_minutes": policy.first_response_minutes,
                    "resolution_minutes": policy.resolution_minutes,
                    "conditions": binding.conditions,
                    "selected_at": occurred_at.isoformat(),
                }
                return

    @staticmethod
    def _matches(binding: ServiceDeskSlaBinding, ticket, service) -> bool:
        for condition in binding.conditions:
            field = condition["field"]
            expected = condition["value"]
            if field == "template_version_id":
                actual = str(ticket.template_version_id)
            elif field == "service_id":
                actual = str(ticket.service_id)
            elif field == "category_id":
                actual = str(service.category_id)
            elif field == "priority":
                actual = ticket.priority.value
            else:
                actual = ticket.field_values.get(condition["field_key"])
            if actual != expected:
                return False
        return True

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
    def _exceptions(
        exceptions: list[schemas.CalendarExceptionInput],
    ) -> list[ServiceDeskCalendarException]:
        return [
            ServiceDeskCalendarException(
                date=exception.date,
                type=exception.type.value,
                start_time=exception.start_time,
                end_time=exception.end_time,
                description=exception.description,
            )
            for exception in exceptions
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

    @staticmethod
    def _validate_exceptions(exceptions: list[schemas.CalendarExceptionInput]) -> None:
        by_date: dict[object, list[schemas.CalendarExceptionInput]] = defaultdict(list)
        for exception in exceptions:
            by_date[exception.date].append(exception)
        for date_exceptions in by_date.values():
            types = {exception.type for exception in date_exceptions}
            if len(types) != 1 or (
                schemas.CalendarExceptionType.CUSTOM_HOURS not in types and len(date_exceptions) > 1
            ):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "One date must have either one day exception or custom hour intervals",
                )
            if schemas.CalendarExceptionType.CUSTOM_HOURS not in types:
                continue
            ordered = sorted(date_exceptions, key=lambda exception: exception.start_time)
            if any(
                current.end_time > following.start_time
                for current, following in zip(ordered, ordered[1:], strict=False)
            ):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Custom hour intervals for one date must not overlap",
                )

    def _require_calendar(self, calendar_id: uuid.UUID) -> ServiceDeskBusinessCalendar:
        calendar = self.repository.get_calendar(calendar_id)
        if not calendar:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Business calendar not found")
        return calendar

    def _require_policy(self, policy_id: uuid.UUID) -> ServiceDeskSlaPolicy:
        policy = self.repository.get_policy(policy_id)
        if not policy:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "SLA policy not found")
        return policy

    def _require_binding(self, binding_id: uuid.UUID) -> ServiceDeskSlaBinding:
        binding = self.repository.get_binding(binding_id)
        if not binding:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "SLA binding not found")
        return binding

    @staticmethod
    def _require_manage_sla(actor: ServiceDeskUser) -> None:
        if any(item.capability == "service_desk.manage_sla" for item in actor.capabilities):
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing service_desk.manage_sla capability")
