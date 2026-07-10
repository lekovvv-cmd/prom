import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ServiceDeskTicketStatus
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.catalog.models import ServiceDeskService
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketCounter, ServiceDeskTicketHistory


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
            .options(
                joinedload(ServiceDeskTicket.history),
                joinedload(ServiceDeskTicket.service).joinedload(ServiceDeskService.category),
                joinedload(ServiceDeskTicket.requester),
                joinedload(ServiceDeskTicket.assignee),
                joinedload(ServiceDeskTicket.approval_stages).joinedload(
                    ServiceDeskTicketApprovalStage.approvals
                ).joinedload(ServiceDeskTicketApproval.approver),
            )
            .where(ServiceDeskTicket.id == ticket_id, ServiceDeskTicket.deleted_at.is_(None))
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def get_ticket_for_update(self, ticket_id: uuid.UUID) -> ServiceDeskTicket | None:
        stmt = (
            select(ServiceDeskTicket)
            .where(ServiceDeskTicket.id == ticket_id, ServiceDeskTicket.deleted_at.is_(None))
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def next_ticket_number(self, year: int) -> str:
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            # Serializes counter creation and increment for the current year.
            self.db.execute(select(func.pg_advisory_xact_lock(year)))

        counter = self.db.get(ServiceDeskTicketCounter, year, with_for_update=True)
        if counter is None:
            counter = ServiceDeskTicketCounter(year=year, last_value=0)
            self.db.add(counter)
            self.db.flush()

        counter.last_value += 1
        self.db.flush()
        return f"SD-{year}-{counter.last_value:06d}"

    def list_user_tickets(
        self,
        requester_user_id: uuid.UUID,
        *,
        status: ServiceDeskTicketStatus | None = None,
    ) -> list[ServiceDeskTicket]:
        stmt = (
            select(ServiceDeskTicket)
            .options(
                joinedload(ServiceDeskTicket.history),
                joinedload(ServiceDeskTicket.service).joinedload(ServiceDeskService.category),
                joinedload(ServiceDeskTicket.requester),
                joinedload(ServiceDeskTicket.assignee),
                joinedload(ServiceDeskTicket.approval_stages).joinedload(
                    ServiceDeskTicketApprovalStage.approvals
                ).joinedload(ServiceDeskTicketApproval.approver),
            )
            .where(
                ServiceDeskTicket.requester_user_id == requester_user_id,
                ServiceDeskTicket.deleted_at.is_(None),
            )
            .order_by(ServiceDeskTicket.created_at.desc())
        )
        if status:
            stmt = stmt.where(ServiceDeskTicket.status == status)
        return list(self.db.scalars(stmt).unique().all())
