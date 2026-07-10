import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.sla.models import ServiceDeskBusinessCalendar


class SlaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_calendars(self) -> list[ServiceDeskBusinessCalendar]:
        statement = (
            select(ServiceDeskBusinessCalendar)
            .options(selectinload(ServiceDeskBusinessCalendar.business_hours))
            .order_by(ServiceDeskBusinessCalendar.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_calendar(self, calendar_id: uuid.UUID) -> ServiceDeskBusinessCalendar | None:
        statement = (
            select(ServiceDeskBusinessCalendar)
            .options(selectinload(ServiceDeskBusinessCalendar.business_hours))
            .where(ServiceDeskBusinessCalendar.id == calendar_id)
        )
        return self.db.scalar(statement)

    def add_calendar(self, calendar: ServiceDeskBusinessCalendar) -> ServiceDeskBusinessCalendar:
        self.db.add(calendar)
        self.db.flush()
        self.db.refresh(calendar)
        return calendar
