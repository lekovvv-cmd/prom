from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import (
    ServiceDeskAccessType,
    ServiceDeskCommentVisibility,
    ServiceDeskTicketAction,
    ServiceDeskTicketStatus,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.comments import schemas
from app.modules.comments.models import ServiceDeskTicketComment
from app.modules.comments.repository import TicketCommentRepository
from app.modules.tickets.lifecycle import TicketLifecycleService
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.policy import TicketPolicyService
from app.modules.tickets.repository import TicketRepository
from app.modules.sla.service import SlaService


FINAL_COMMENT_STATUSES = {
    ServiceDeskTicketStatus.CLOSED,
    ServiceDeskTicketStatus.CANCELLED,
}


class TicketCommentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TicketCommentRepository(db)
        self.ticket_repository = TicketRepository(db)
        self.policy = TicketPolicyService()
        self.lifecycle = TicketLifecycleService(self.ticket_repository)
        self.sla_service = SlaService(db)

    def list_comments(
        self,
        ticket_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskTicketComment]:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        comments = self.repository.list_for_ticket(ticket.id)
        if self.policy.can_view_internal_comments(ticket, actor):
            return comments
        return [item for item in comments if item.visibility == ServiceDeskCommentVisibility.PUBLIC]

    def create_comment(
        self,
        ticket_id: uuid.UUID,
        payload: schemas.TicketCommentCreate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskTicketComment:
        ticket = self._require_ticket_for_update(ticket_id)
        self.policy.require_view(ticket, actor)
        self._ensure_ticket_accepts_comments(ticket)
        if payload.visibility == ServiceDeskCommentVisibility.INTERNAL:
            self.policy.require_internal_comments(ticket, actor)

        comment = self.repository.add(
            ServiceDeskTicketComment(
                ticket_id=ticket.id,
                author_user_id=actor.id,
                body=payload.body.strip(),
                visibility=payload.visibility,
            )
        )
        self._write_history(ticket, "comment_added", actor, comment)
        now = datetime.now(UTC)
        if (
            payload.visibility == ServiceDeskCommentVisibility.PUBLIC
            and actor.id == ticket.assignee_user_id
        ):
            self.sla_service.mark_first_response(ticket, actor=actor, occurred_at=now)
        if (
            payload.visibility == ServiceDeskCommentVisibility.PUBLIC
            and actor.id == ticket.requester_user_id
            and ticket.status == ServiceDeskTicketStatus.WAITING_REQUESTER
        ):
            previous_status = ticket.status
            self.lifecycle.perform_transition(
                ticket,
                ServiceDeskTicketAction.REQUESTER_REPLY,
                actor=actor,
                occurred_at=now,
            )
            self.sla_service.handle_transition(
                ticket, previous_status, actor=actor, occurred_at=now
            )
        self.db.commit()
        return comment

    def update_comment(
        self,
        ticket_id: uuid.UUID,
        comment_id: uuid.UUID,
        payload: schemas.TicketCommentUpdate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskTicketComment:
        ticket = self._require_ticket_for_update(ticket_id)
        comment = self._require_comment_for_ticket(comment_id, ticket.id)
        self._require_comment_editor(ticket, comment, actor)
        self._ensure_ticket_accepts_comments(ticket)
        comment.body = payload.body.strip()
        comment.updated_at = datetime.now(UTC)
        self._write_history(ticket, "comment_updated", actor, comment)
        self.db.commit()
        return comment

    def delete_comment(
        self,
        ticket_id: uuid.UUID,
        comment_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> None:
        ticket = self._require_ticket_for_update(ticket_id)
        comment = self._require_comment_for_ticket(comment_id, ticket.id)
        self._require_comment_editor(ticket, comment, actor)
        self._ensure_ticket_accepts_comments(ticket)
        comment.deleted_at = datetime.now(UTC)
        self._write_history(ticket, "comment_deleted", actor, comment)
        self.db.commit()

    def _require_comment_editor(
        self,
        ticket: ServiceDeskTicket,
        comment: ServiceDeskTicketComment,
        actor: ServiceDeskUser,
    ) -> None:
        if comment.visibility == ServiceDeskCommentVisibility.INTERNAL:
            self.policy.require_internal_comments(ticket, actor)
        else:
            self.policy.require_view(ticket, actor)
        if actor.id == comment.author_user_id or actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Изменять комментарий может только автор или администратор")

    def _require_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.ticket_repository.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    def _require_ticket_for_update(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.ticket_repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    def _require_comment_for_ticket(
        self,
        comment_id: uuid.UUID,
        ticket_id: uuid.UUID,
    ) -> ServiceDeskTicketComment:
        comment = self.repository.get_for_update(comment_id)
        if not comment or comment.ticket_id != ticket_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Комментарий не найден")
        return comment

    @staticmethod
    def _ensure_ticket_accepts_comments(ticket: ServiceDeskTicket) -> None:
        if ticket.status in FINAL_COMMENT_STATUSES:
            raise HTTPException(status.HTTP_409_CONFLICT, "Закрытую заявку нельзя комментировать")

    def _write_history(
        self,
        ticket: ServiceDeskTicket,
        event_type: str,
        actor: ServiceDeskUser,
        comment: ServiceDeskTicketComment,
    ) -> None:
        message = {
            "comment_added": "Добавлен комментарий",
            "comment_updated": "Комментарий изменён",
            "comment_deleted": "Комментарий удалён",
        }[event_type]
        self.ticket_repository.add_history(
            ServiceDeskTicketHistory(
                ticket_id=ticket.id,
                event_type=event_type,
                actor_user_id=actor.id,
                message=message,
                payload={
                    "comment_id": str(comment.id),
                    "comment_visibility": comment.visibility.value,
                },
            )
        )
