import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import (
    ServiceDeskTicketAction,
    ServiceDeskTicketStatus,
    TemplateFieldType,
    TemplateVersionStatus,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.assignments.policy import AssigneePolicy
from app.modules.approvals import schemas as approval_schemas
from app.modules.approvals.models import ServiceDeskTicketApprovalStage
from app.modules.approvals.ticket_service import TicketApprovalService
from app.modules.attachments.service import AttachmentService
from app.modules.catalog.repository import CatalogRepository
from app.modules.routing.service import RoutingService
from app.modules.sla.service import SlaService
from app.modules.templates.models import ServiceDeskTemplateVersion
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.validation import validate_template_payload
from app.modules.tickets import schemas
from app.modules.tickets.lifecycle import TicketLifecycleService
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.policy import TicketPolicyService
from app.modules.tickets.repository import TicketRepository


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TicketRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.template_repository = TemplateRepository(db)
        self.lifecycle = TicketLifecycleService(self.repository)
        self.ticket_approval_service = TicketApprovalService(db, self.repository)
        self.attachment_service = AttachmentService(db)
        self.routing_service = RoutingService(db, self.repository)
        self.sla_service = SlaService(db)
        self.policy = TicketPolicyService()

    def create_draft(
        self,
        payload: schemas.TicketDraftCreate,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
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
            requester_user_id=actor.id,
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
            actor.id,
            "Заявка создана как черновик",
            {"status": ticket.status.value},
        )
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def update_draft(
        self,
        ticket_id: uuid.UUID,
        payload: schemas.TicketDraftUpdate,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self._require_ticket(ticket_id)
        if ticket.requester_user_id != actor.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Редактировать черновик может только заявитель"
            )
        if ticket.status != ServiceDeskTicketStatus.DRAFT:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Редактировать можно только черновик заявки"
            )
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(ticket, field, value)
        self._write_history(
            ticket,
            "ticket_updated",
            actor.id,
            "Черновик заявки обновлён",
            {"changed_fields": sorted(data.keys())},
        )
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def submit_draft(self, ticket_id: uuid.UUID, actor: ServiceDeskUser) -> schemas.TicketRead:
        ticket = self.repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        if ticket.requester_user_id != actor.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Отправить черновик может только заявитель"
            )
        if ticket.status != ServiceDeskTicketStatus.DRAFT:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Отправить можно только черновик заявки",
            )

        service = self.catalog_repository.get_service(ticket.service_id)
        if not service or not service.is_active or service.deleted_at is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Услуга больше недоступна")

        template_version = self.template_repository.get_version(ticket.template_version_id)
        if not template_version or template_version.service_id != ticket.service_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Шаблон услуги больше недоступен")
        if template_version.status == TemplateVersionStatus.DRAFT:
            raise HTTPException(status.HTTP_409_CONFLICT, "Форма услуги ещё не опубликована")

        field_values = self._field_values_with_uploaded_files(ticket, template_version)
        validation = validate_template_payload(
            template_version,
            field_values,
            dictionary_options=self._dictionary_options(template_version),
        )
        errors = self._validate_system_fields(ticket, template_version.system_settings)
        errors.extend(error.model_dump() for error in validation.errors)
        if errors:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Проверьте заполнение формы", "errors": errors},
            )

        default_title = template_version.system_settings.get("default_title")
        if not template_version.system_settings.get("is_title_editable", True) and default_title:
            ticket.title = str(default_title)
        ticket.field_values = validation.normalized_data
        now = datetime.now(UTC)
        ticket.number = self.repository.next_ticket_number(now.year)
        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.SUBMIT,
            actor=actor,
            metadata={"number": ticket.number},
            occurred_at=now,
        )
        self.routing_service.snapshot_ticket(ticket, service, occurred_at=now)
        self.sla_service.snapshot_ticket(ticket, service, occurred_at=now)
        self.ticket_approval_service.initialize_snapshot(
            ticket,
            template_version,
            occurred_at=now,
        )
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def perform_action(
        self,
        ticket_id: uuid.UUID,
        action: ServiceDeskTicketAction,
        actor: ServiceDeskUser,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> schemas.TicketRead:
        ticket = self.repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        previous_status = ticket.status
        now = datetime.now(UTC)
        self.lifecycle.perform_transition(ticket, action, actor=actor, metadata=metadata, occurred_at=now)
        self.sla_service.handle_transition(ticket, previous_status, actor=actor, occurred_at=now)
        if action in {ServiceDeskTicketAction.START, ServiceDeskTicketAction.REQUEST_CLARIFICATION}:
            self.sla_service.mark_first_response(ticket, actor=actor, occurred_at=now)
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def assign_ticket(
        self,
        ticket_id: uuid.UUID,
        payload: schemas.TicketAssignmentAction,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self._require_ticket_for_update(ticket_id)
        if ticket.assignee_user_id is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "У заявки уже назначен исполнитель")
        assignee = AssigneePolicy(self.db).require_eligible_assignee(payload.assignee_user_id)
        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.ASSIGN,
            actor=actor,
            metadata={
                "assignee_user_id": str(assignee.id),
                "assignment_source": "manual",
            },
        )
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def reassign_ticket(
        self,
        ticket_id: uuid.UUID,
        payload: schemas.TicketAssignmentAction,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self._require_ticket_for_update(ticket_id)
        if ticket.assignee_user_id is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "У заявки нет назначенного исполнителя")
        if ticket.assignee_user_id == payload.assignee_user_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Исполнитель уже назначен на заявку")
        assignee = AssigneePolicy(self.db).require_eligible_assignee(payload.assignee_user_id)
        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.REASSIGN,
            actor=actor,
            metadata={
                "assignee_user_id": str(assignee.id),
                "previous_assignee_user_id": str(ticket.assignee_user_id),
                "assignment_source": "manual",
            },
        )
        self.db.commit()
        return self._read_for_actor(self._require_ticket(ticket.id), actor)

    def list_user_tickets(
        self,
        actor: ServiceDeskUser,
        *,
        status_filter: ServiceDeskTicketStatus | None = None,
    ) -> list[schemas.TicketRead]:
        tickets = self.repository.list_user_tickets(actor.id, status=status_filter)
        return [self._read_for_actor(ticket, actor) for ticket in tickets]

    def get_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        return self._require_ticket(ticket_id)

    def get_ticket_for_actor(
        self,
        ticket_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        return self._read_for_actor(ticket, actor)

    def get_approval_snapshot(
        self,
        ticket_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskTicketApprovalStage]:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        return self.ticket_approval_service.get_snapshot(ticket_id)

    def approve_ticket(
        self,
        ticket_id: uuid.UUID,
        approval_id: uuid.UUID,
        payload: approval_schemas.TicketApprovalDecision,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self.ticket_approval_service.approve(
            ticket_id,
            approval_id,
            actor.id,
            comment=payload.comment,
        )
        return self._read_for_actor(ticket, actor)

    def reject_ticket(
        self,
        ticket_id: uuid.UUID,
        approval_id: uuid.UUID,
        payload: approval_schemas.TicketApprovalRejection,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        ticket = self.ticket_approval_service.reject(
            ticket_id,
            approval_id,
            actor.id,
            comment=payload.comment,
        )
        return self._read_for_actor(ticket, actor)

    def _read_for_actor(
        self,
        ticket: ServiceDeskTicket,
        actor: ServiceDeskUser,
    ) -> schemas.TicketRead:
        read = schemas.TicketRead.model_validate(ticket)
        if not self.policy.can_view_internal_comments(ticket, actor):
            read = read.model_copy(
                update={
                    "comments": [
                        comment for comment in read.comments if comment.visibility == "public"
                    ],
                    "history": [
                        item
                        for item in read.history
                        if item.payload.get("comment_visibility") != "internal"
                    ],
                }
            )
        return read.model_copy(
            update={
                "allowed_actions": self.policy.allowed_actions(ticket, actor),
                "field_snapshot": self._field_snapshot(ticket),
            }
        )

    def _field_snapshot(self, ticket: ServiceDeskTicket) -> list[schemas.TicketFieldSnapshotRead]:
        template_version = ticket.template_version or self.template_repository.get_version(ticket.template_version_id)
        if not template_version:
            return []
        dictionary_labels: dict[str, dict[str, str]] = {}
        for field in template_version.fields:
            if not field.dictionary_code or field.dictionary_code in dictionary_labels:
                continue
            dictionary = self.template_repository.get_dictionary_by_code(field.dictionary_code)
            dictionary_labels[field.dictionary_code] = {
                item.value: item.label for item in dictionary.items if item.is_active
            } if dictionary else {}
        snapshots: list[schemas.TicketFieldSnapshotRead] = []
        for field in sorted(template_version.fields, key=lambda item: (item.position, item.label)):
            raw_value = ticket.field_values.get(field.key)
            display_value = self._display_field_value(field, raw_value, dictionary_labels)
            snapshots.append(
                schemas.TicketFieldSnapshotRead(
                    key=field.key,
                    label=field.label,
                    type=field.field_type.value,
                    raw_value=raw_value,
                    display_value=display_value,
                )
            )
        return snapshots

    @staticmethod
    def _display_field_value(field, raw_value: Any, dictionary_labels: dict[str, dict[str, str]]) -> str:
        if raw_value is None or raw_value == "" or raw_value == []:
            return "Не указано"
        option_labels = {
            str(item.get("value")): str(item.get("label", item.get("value")))
            for item in (field.options or [])
            if isinstance(item, dict) and item.get("value") is not None
        }
        if field.dictionary_code:
            option_labels.update(dictionary_labels.get(field.dictionary_code, {}))
        if isinstance(raw_value, list):
            values: list[str] = []
            for item in raw_value:
                if isinstance(item, dict):
                    values.append(str(item.get("name") or item.get("label") or item.get("value") or "Не указано"))
                else:
                    values.append(option_labels.get(str(item), str(item)))
            return ", ".join(values)
        if isinstance(raw_value, bool):
            return "Да" if raw_value else "Нет"
        if isinstance(raw_value, dict):
            return str(raw_value.get("name") or raw_value.get("label") or raw_value.get("value") or "Не указано")
        return option_labels.get(str(raw_value), str(raw_value))

    def _require_active_user(self, user_id: uuid.UUID) -> ServiceDeskUser:
        user = self.db.get(ServiceDeskUser, user_id)
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
        return user

    def _require_ticket_for_update(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    def _require_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.repository.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    def _dictionary_options(
        self,
        template_version: ServiceDeskTemplateVersion,
    ) -> dict[str, set[Any]]:
        options: dict[str, set[Any]] = {}
        dictionary_codes = {
            field.dictionary_code for field in template_version.fields if field.dictionary_code
        }
        for code in dictionary_codes:
            dictionary = self.template_repository.get_dictionary_by_code(code)
            if not dictionary or not dictionary.is_active:
                options[code] = set()
                continue
            options[code] = {item.value for item in dictionary.items if item.is_active}
        return options

    def _field_values_with_uploaded_files(
        self,
        ticket: ServiceDeskTicket,
        template_version: ServiceDeskTemplateVersion,
    ) -> dict[str, Any]:
        field_values = dict(ticket.field_values)
        uploaded_files = self.attachment_service.field_value_payload(ticket.id)
        for field in template_version.fields:
            if field.field_type == TemplateFieldType.FILE:
                field_values[field.key] = uploaded_files.get(field.key, [])
        return field_values

    @staticmethod
    def _validate_system_fields(
        ticket: ServiceDeskTicket,
        system_settings: dict[str, Any],
    ) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        if not isinstance(ticket.title, str) or len(ticket.title.strip()) < 2:
            errors.append({"field_key": "title", "message": "Тема: Заполните обязательное поле"})
        if system_settings.get("is_description_required", True) and (
            not isinstance(ticket.description, str) or not ticket.description.strip()
        ):
            errors.append(
                {"field_key": "description", "message": "Описание: Заполните обязательное поле"}
            )
        return errors

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
