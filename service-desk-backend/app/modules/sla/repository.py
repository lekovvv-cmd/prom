import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.sla.models import (
    ServiceDeskBusinessCalendar,
    ServiceDeskSlaBinding,
    ServiceDeskSlaPolicy,
)


class SlaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_calendars(self) -> list[ServiceDeskBusinessCalendar]:
        statement = (
            select(ServiceDeskBusinessCalendar)
            .options(
                selectinload(ServiceDeskBusinessCalendar.business_hours),
                selectinload(ServiceDeskBusinessCalendar.exceptions),
            )
            .order_by(ServiceDeskBusinessCalendar.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_calendar(self, calendar_id: uuid.UUID) -> ServiceDeskBusinessCalendar | None:
        statement = (
            select(ServiceDeskBusinessCalendar)
            .options(
                selectinload(ServiceDeskBusinessCalendar.business_hours),
                selectinload(ServiceDeskBusinessCalendar.exceptions),
            )
            .where(ServiceDeskBusinessCalendar.id == calendar_id)
        )
        return self.db.scalar(statement)

    def add_calendar(self, calendar: ServiceDeskBusinessCalendar) -> ServiceDeskBusinessCalendar:
        self.db.add(calendar)
        self.db.flush()
        self.db.refresh(calendar)
        return calendar

    def list_policies(self) -> list[ServiceDeskSlaPolicy]:
        return list(
            self.db.scalars(select(ServiceDeskSlaPolicy).order_by(ServiceDeskSlaPolicy.name)).all()
        )

    def get_policy(self, policy_id: uuid.UUID) -> ServiceDeskSlaPolicy | None:
        return self.db.get(ServiceDeskSlaPolicy, policy_id)

    def add_policy(self, policy: ServiceDeskSlaPolicy) -> ServiceDeskSlaPolicy:
        self.db.add(policy)
        self.db.flush()
        return policy

    def list_bindings(self, *, active_only: bool = False) -> list[ServiceDeskSlaBinding]:
        statement = select(ServiceDeskSlaBinding).options(
            selectinload(ServiceDeskSlaBinding.policy)
        )
        if active_only:
            statement = statement.where(ServiceDeskSlaBinding.is_active.is_(True))
        statement = statement.order_by(
            ServiceDeskSlaBinding.priority, ServiceDeskSlaBinding.created_at
        )
        return list(self.db.scalars(statement).all())

    def get_binding(self, binding_id: uuid.UUID) -> ServiceDeskSlaBinding | None:
        return self.db.get(ServiceDeskSlaBinding, binding_id)

    def add_binding(self, binding: ServiceDeskSlaBinding) -> ServiceDeskSlaBinding:
        self.db.add(binding)
        self.db.flush()
        return binding
