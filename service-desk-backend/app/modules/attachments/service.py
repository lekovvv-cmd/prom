from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import ServiceDeskAttachmentOwnerType, ServiceDeskCommentVisibility
from app.modules.access.models import ServiceDeskUser
from app.modules.attachments.models import ServiceDeskAttachment
from app.modules.attachments.repository import AttachmentRepository
from app.modules.comments.repository import TicketCommentRepository
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.policy import TicketPolicyService
from app.modules.tickets.repository import TicketRepository


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "image/png",
    "image/jpeg",
    "application/zip",
}


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AttachmentRepository(db)
        self.ticket_repository = TicketRepository(db)
        self.comment_repository = TicketCommentRepository(db)
        self.policy = TicketPolicyService()

    async def upload_ticket_attachment(
        self,
        ticket_id: uuid.UUID,
        file: UploadFile,
        actor: ServiceDeskUser,
    ) -> ServiceDeskAttachment:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        return await self._store(
            owner_type=ServiceDeskAttachmentOwnerType.TICKET,
            owner_id=ticket.id,
            ticket=ticket,
            file=file,
            actor=actor,
            comment_visibility=None,
        )

    async def upload_comment_attachment(
        self,
        ticket_id: uuid.UUID,
        comment_id: uuid.UUID,
        file: UploadFile,
        actor: ServiceDeskUser,
    ) -> ServiceDeskAttachment:
        ticket = self._require_ticket(ticket_id)
        comment = self.comment_repository.get_for_update(comment_id)
        if not comment or comment.ticket_id != ticket.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Комментарий не найден")
        self.policy.require_view(ticket, actor)
        if comment.visibility == ServiceDeskCommentVisibility.INTERNAL:
            self.policy.require_internal_comments(ticket, actor)
        return await self._store(
            owner_type=ServiceDeskAttachmentOwnerType.COMMENT,
            owner_id=comment.id,
            ticket=ticket,
            file=file,
            actor=actor,
            comment_visibility=comment.visibility,
        )

    def list_ticket_attachments(
        self,
        ticket_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskAttachment]:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        return self.repository.list_for_owner(ServiceDeskAttachmentOwnerType.TICKET, ticket.id)

    def list_comment_attachments(
        self,
        ticket_id: uuid.UUID,
        comment_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskAttachment]:
        ticket = self._require_ticket(ticket_id)
        comment = self.comment_repository.get_for_update(comment_id)
        if not comment or comment.ticket_id != ticket.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Комментарий не найден")
        self.policy.require_view(ticket, actor)
        if comment.visibility == ServiceDeskCommentVisibility.INTERNAL:
            self.policy.require_internal_comments(ticket, actor)
        return self.repository.list_for_owner(ServiceDeskAttachmentOwnerType.COMMENT, comment.id)

    async def _store(
        self,
        *,
        owner_type: ServiceDeskAttachmentOwnerType,
        owner_id: uuid.UUID,
        ticket: ServiceDeskTicket,
        file: UploadFile,
        actor: ServiceDeskUser,
        comment_visibility: ServiceDeskCommentVisibility | None,
    ) -> ServiceDeskAttachment:
        if self.repository.count_for_owner(owner_type, owner_id) >= settings.max_attachments_per_owner:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Превышен лимит вложений")
        file_name, extension = self._validate_file_metadata(file)
        payload = await file.read()
        if not payload:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Нельзя прикрепить пустой файл")
        if len(payload) > settings.max_attachment_size_bytes:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Файл превышает допустимый размер")

        storage_key = f"{owner_type.value}/{owner_id}/{uuid.uuid4().hex}{extension}"
        path = self._storage_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        attachment = self.repository.add(
            ServiceDeskAttachment(
                owner_type=owner_type,
                owner_id=owner_id,
                ticket_id=ticket.id,
                file_name=file_name,
                storage_key=storage_key,
                content_type=file.content_type,
                size_bytes=len(payload),
                uploaded_by_user_id=actor.id,
            )
        )
        self.ticket_repository.add_history(
            ServiceDeskTicketHistory(
                ticket_id=ticket.id,
                event_type="attachment_uploaded",
                actor_user_id=actor.id,
                message="Добавлено вложение",
                payload={
                    "attachment_id": str(attachment.id),
                    "owner_type": owner_type.value,
                    "owner_id": str(owner_id),
                    "file_name": file_name,
                    "comment_visibility": comment_visibility.value if comment_visibility else None,
                },
            )
        )
        self.db.commit()
        return attachment

    @staticmethod
    def _validate_file_metadata(file: UploadFile) -> tuple[str, str]:
        file_name = AttachmentService._sanitize_file_name(file.filename or "attachment")
        extension = Path(file_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимое расширение файла")
        if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимый MIME-тип файла")
        guessed_type, _ = mimetypes.guess_type(file_name)
        if guessed_type and file.content_type and guessed_type != file.content_type:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "MIME-тип не соответствует расширению")
        return file_name, extension

    @staticmethod
    def _sanitize_file_name(file_name: str) -> str:
        clean = re.sub(r"[\\/:*?\"<>|]+", "_", file_name).strip(". ")
        return clean[:255] or "attachment"

    @staticmethod
    def _storage_path(storage_key: str) -> Path:
        root = Path(settings.storage_dir).resolve()
        path = (root / storage_key).resolve()
        if root not in path.parents:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимый путь вложения")
        return path

    def _require_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.ticket_repository.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket
