import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.repository import CatalogRepository
from app.modules.templates.repository import TemplateRepository
from app.modules.tickets import schemas
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.repository import TicketRepository


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TicketRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.template_repository = TemplateRepository(db)

    def create_draft(self, payload: schemas.TicketDraftCreate) -> ServiceDeskTicket:
        requester = self._require_active_user(payload.requester_user_id)
        service = self.catalog_repository.get_service(payload.service_id)
        if not service or not service.is_active or service.deleted_at is not None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")

        template_version = (
            self.template_repository.get_version(payload.template_version_id)
            if payload.template_version_id
            else self.template_repository.get_published_version(payload.service_id)
        )
        if not template_version or template_version.service_id != payload.service_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Шаблон услуги не найден")

        ticket = ServiceDeskTicket(
            service_id=payload.service_id,
            template_version_id=template_version.id,
            requester_user_id=requester.id,
            title=payload.title,
            description=payload.description,
            status=ServiceDeskTicketStatus.DRAFT,
            priority=payload.priority,
            field_values=payload.field_values,
        )
        self.repository.add_ticket(ticket)
        self._write_history(
            ticket,
            "ticket_created",
            requester.id,
            "Заявка создана как черновик",
            {"status": ticket.status.value},
        )
        self.db.commit()
        return self._require_ticket(ticket.id)

    def update_draft(self, ticket_id: uuid.UUID, payload: schemas.TicketDraftUpdate) -> ServiceDeskTicket:
        ticket = self._require_ticket(ticket_id)
        if ticket.status != ServiceDeskTicketStatus.DRAFT:
            raise HTTPException(status.HTTP_409_CONFLICT, "Редактировать можно только черновик заявки")
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(ticket, field, value)
        self._write_history(
            ticket,
            "ticket_updated",
            ticket.requester_user_id,
            "Черновик заявки обновлён",
            {"changed_fields": sorted(data.keys())},
        )
        self.db.commit()
        return self._require_ticket(ticket.id)

    def list_user_tickets(
        self,
        requester_user_id: uuid.UUID,
        *,
        status_filter: ServiceDeskTicketStatus | None = None,
    ) -> list[ServiceDeskTicket]:
        self._require_active_user(requester_user_id)
        return self.repository.list_user_tickets(requester_user_id, status=status_filter)

    def get_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        return self._require_ticket(ticket_id)

    def _require_active_user(self, user_id: uuid.UUID) -> ServiceDeskUser:
        user = self.db.get(ServiceDeskUser, user_id)
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
        return user

    def _require_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.repository.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    def _write_history(
        self,
        ticket: ServiceDeskTicket,
        event_type: str,
        actor_user_id: uuid.UUID | None,
        message: str,
        payload: dict,
    ) -> None:
        self.repository.add_history(
            ServiceDeskTicketHistory(
                ticket_id=ticket.id,
                event_type=event_type,
                actor_user_id=actor_user_id,
                message=message,
                payload=payload,
            )
        )
