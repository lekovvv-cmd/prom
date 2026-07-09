import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ServiceDeskTicketStatus
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_ticket(self, ticket: ServiceDeskTicket) -> ServiceDeskTicket:
        self.db.add(ticket)
        self.db.flush()
        self.db.refresh(ticket)
        return ticket

    def add_history(self, history: ServiceDeskTicketHistory) -> ServiceDeskTicketHistory:
        self.db.add(history)
        self.db.flush()
        return history

    def get_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket | None:
        stmt = (
            select(ServiceDeskTicket)
            .options(joinedload(ServiceDeskTicket.history))
            .where(ServiceDeskTicket.id == ticket_id, ServiceDeskTicket.deleted_at.is_(None))
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def list_user_tickets(
        self,
        requester_user_id: uuid.UUID,
        *,
        status: ServiceDeskTicketStatus | None = None,
    ) -> list[ServiceDeskTicket]:
        stmt = (
            select(ServiceDeskTicket)
            .options(joinedload(ServiceDeskTicket.history))
            .where(
                ServiceDeskTicket.requester_user_id == requester_user_id,
                ServiceDeskTicket.deleted_at.is_(None),
            )
            .order_by(ServiceDeskTicket.created_at.desc())
        )
        if status:
            stmt = stmt.where(ServiceDeskTicket.status == status)
        return list(self.db.scalars(stmt).unique().all())
