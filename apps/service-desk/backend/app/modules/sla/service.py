from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import time

from platform_sdk.error_types import EntityNotFound, PermissionDenied, ValidationFailed
from sqlalchemy.orm import Session

from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService
from app.modules.sla import schemas
from app.modules.sla.engine import (
    add_business_minutes,
    add_business_seconds,
    business_seconds_between,
)
from app.modules.sla.models import (
    ServiceDeskBusinessCalendar,
    ServiceDeskBusinessHours,
    ServiceDeskCalendarException,
    ServiceDeskEscalationRule,
    ServiceDeskSlaBinding,
    ServiceDeskSlaPolicy,
    ServiceDeskTicketSlaPause,
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
        if "timezone" in data and payload.timezone is not None:
            calendar.timezone = payload.timezone
        if "is_active" in data and payload.is_active is not None:
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

    def list_escalations(self, actor, policy_id=None):
        self._require_manage_sla(actor)
        return self.repository.list_escalations(policy_id)

    def list_recipients(self, actor):
        self._require_manage_sla(actor)
        return self.repository.list_recipients()

    def create_escalation(self, policy_id, payload, actor):
        self._require_manage_sla(actor)
        self._require_policy(policy_id)
        self._validate_escalation_recipient(payload)
        rule = ServiceDeskEscalationRule(sla_policy_id=policy_id, **payload.model_dump())
        self.db.add(rule)
        self.db.commit()
        return rule

    def update_escalation(self, rule_id, payload, actor):
        self._require_manage_sla(actor)
        rule = self.db.get(ServiceDeskEscalationRule, rule_id)
        if not rule:
            raise EntityNotFound("Правило эскалации не найдено")
        data = payload.model_dump(exclude_unset=True)
        definition = schemas.EscalationRuleCreate.model_validate(
            {
                "metric": rule.metric,
                "threshold_percent": rule.threshold_percent,
                "action_type": rule.action_type,
                "recipient_type": rule.recipient_type,
                "recipient_user_id": rule.recipient_user_id,
                "is_active": rule.is_active,
                **data,
            }
        )
        self._validate_escalation_recipient(definition)
        for field, value in data.items():
            setattr(rule, field, value)
        self.db.commit()
        return rule

    def delete_escalation(self, rule_id, actor):
        self._require_manage_sla(actor)
        rule = self.db.get(ServiceDeskEscalationRule, rule_id)
        if not rule:
            raise EntityNotFound("Правило эскалации не найдено")
        self.db.delete(rule)
        self.db.commit()

    def _validate_escalation_recipient(self, payload: schemas.EscalationRuleCreate) -> None:
        if payload.recipient_user_id is None:
            return
        recipient = self.db.get(ServiceDeskUser, payload.recipient_user_id)
        if not recipient or not recipient.is_active:
            raise ValidationFailed("Escalation recipient is unavailable")

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
                    "pause_statuses": policy.pause_statuses,
                    "business_hours": [
                        {"weekday": item.weekday, "start_time": item.start_time.isoformat(), "end_time": item.end_time.isoformat()}
                        for item in calendar.business_hours
                    ],
                    "calendar_exceptions": [
                        {"date": item.date.isoformat(), "type": item.type, "start_time": item.start_time.isoformat() if item.start_time else None, "end_time": item.end_time.isoformat() if item.end_time else None}
                        for item in calendar.exceptions
                    ],
                    "conditions": binding.conditions,
                    "selected_at": occurred_at.isoformat(),
                }
                ticket.sla_policy_id = policy.id
                ticket.first_response_due_at = add_business_minutes(
                    occurred_at, policy.first_response_minutes, ticket.sla_snapshot
                )
                ticket.resolution_due_at = add_business_minutes(
                    occurred_at, policy.resolution_minutes, ticket.sla_snapshot
                )
                return

    def handle_transition(self, ticket, previous_status, *, actor, occurred_at) -> None:
        if not ticket.sla_snapshot or ticket.resolved_at:
            return
        pause_statuses = set(ticket.sla_snapshot.get("pause_statuses", []))
        was_paused = previous_status.value in pause_statuses
        is_paused = ticket.status.value in pause_statuses
        active = self.db.query(ServiceDeskTicketSlaPause).filter_by(
            ticket_id=ticket.id, ended_at=None
        ).with_for_update().one_or_none()
        if is_paused and not was_paused:
            if active is None:
                self.db.add(ServiceDeskTicketSlaPause(
                    ticket_id=ticket.id, reason_status=ticket.status.value, started_at=occurred_at
                ))
                self._sla_history(ticket, "sla_paused", actor, {"reason_status": ticket.status.value})
        elif was_paused and not is_paused and active is not None:
            duration = max(0, int((occurred_at - active.started_at).total_seconds()))
            active.ended_at = occurred_at
            active.duration_seconds = duration
            ticket.paused_seconds += duration
            lost = business_seconds_between(active.started_at, occurred_at, ticket.sla_snapshot)
            if ticket.resolution_due_at and lost:
                ticket.resolution_due_at = add_business_seconds(
                    ticket.resolution_due_at, lost, ticket.sla_snapshot
                )
            self._sla_history(ticket, "sla_resumed", actor, {"duration_seconds": duration})

    def mark_first_response(self, ticket, *, actor, occurred_at) -> None:
        if ticket.sla_snapshot and ticket.first_response_at is None:
            ticket.first_response_at = occurred_at
            self._sla_history(ticket, "sla_first_response", actor, {})

    def _sla_history(self, ticket, event_type, actor, payload) -> None:
        from app.modules.tickets.models import ServiceDeskTicketHistory
        self.db.add(ServiceDeskTicketHistory(
            ticket_id=ticket.id, event_type=event_type,
            actor_user_id=actor.id if actor else None, message=event_type.replace("_", " "),
            payload=payload,
        ))

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
                raise ValidationFailed("Business hour intervals for one weekday must not overlap",
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
                raise ValidationFailed("One date must have either one day exception or custom hour intervals",
                )
            if schemas.CalendarExceptionType.CUSTOM_HOURS not in types:
                continue
            intervals: list[tuple[time, time]] = []
            for exception in date_exceptions:
                if exception.start_time is None or exception.end_time is None:
                    raise ValidationFailed(
                        "Custom hour intervals require start_time and end_time"
                    )
                intervals.append((exception.start_time, exception.end_time))
            ordered = sorted(intervals)
            if any(
                current[1] > following[0]
                for current, following in zip(ordered, ordered[1:], strict=False)
            ):
                raise ValidationFailed("Custom hour intervals for one date must not overlap",
                )

    def _require_calendar(self, calendar_id: uuid.UUID) -> ServiceDeskBusinessCalendar:
        calendar = self.repository.get_calendar(calendar_id)
        if not calendar:
            raise EntityNotFound("Рабочий календарь не найден")
        return calendar

    def _require_policy(self, policy_id: uuid.UUID) -> ServiceDeskSlaPolicy:
        policy = self.repository.get_policy(policy_id)
        if not policy:
            raise EntityNotFound("Политика SLA не найдена")
        return policy

    def _require_binding(self, binding_id: uuid.UUID) -> ServiceDeskSlaBinding:
        binding = self.repository.get_binding(binding_id)
        if not binding:
            raise EntityNotFound("Правило применения SLA не найдено")
        return binding

    @staticmethod
    def _require_manage_sla(actor: ServiceDeskUser) -> None:
        if "service_desk.manage_sla" in ServiceDeskAccessService.capabilities_for(actor):
            return
        raise PermissionDenied("Недостаточно прав для настройки SLA Service Desk")
