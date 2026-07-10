import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.comments.models import ServiceDeskTicketComment


class TicketCommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, comment: ServiceDeskTicketComment) -> ServiceDeskTicketComment:
        self.db.add(comment)
        self.db.flush()
        self.db.refresh(comment)
        return comment

    def list_for_ticket(self, ticket_id: uuid.UUID) -> list[ServiceDeskTicketComment]:
        statement = (
            select(ServiceDeskTicketComment)
            .options(joinedload(ServiceDeskTicketComment.author))
            .where(
                ServiceDeskTicketComment.ticket_id == ticket_id,
                ServiceDeskTicketComment.deleted_at.is_(None),
            )
            .order_by(ServiceDeskTicketComment.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_for_update(self, comment_id: uuid.UUID) -> ServiceDeskTicketComment | None:
        statement = (
            select(ServiceDeskTicketComment)
            .where(ServiceDeskTicketComment.id == comment_id, ServiceDeskTicketComment.deleted_at.is_(None))
            .with_for_update()
        )
        return self.db.scalar(statement)
