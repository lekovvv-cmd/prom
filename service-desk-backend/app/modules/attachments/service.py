from __future__ import annotations

import codecs
import re
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import (
    ServiceDeskAccessType,
    ServiceDeskAttachmentOwnerType,
    ServiceDeskCommentVisibility,
    ServiceDeskTicketStatus,
    TemplateFieldType,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.attachments.models import ServiceDeskAttachment
from app.modules.attachments.repository import AttachmentRepository
from app.modules.comments.repository import TicketCommentRepository
from app.modules.templates.repository import TemplateRepository
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.policy import TicketPolicyService
from app.modules.tickets.repository import TicketRepository


UPLOAD_CHUNK_SIZE = 64 * 1024
MAX_ARCHIVE_ENTRIES = 10_000

CONTENT_TYPE_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".zip": "application/zip",
}
ALLOWED_EXTENSIONS = set(CONTENT_TYPE_BY_EXTENSION)
ALLOWED_CONTENT_TYPES = set(CONTENT_TYPE_BY_EXTENSION.values())
OOXML_MAIN_PART_BY_EXTENSION = {
    ".docx": "word/document.xml",
    ".xlsx": "xl/workbook.xml",
    ".pptx": "ppt/presentation.xml",
}
OLE_COMPOUND_FILE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AttachmentRepository(db)
        self.ticket_repository = TicketRepository(db)
        self.comment_repository = TicketCommentRepository(db)
        self.template_repository = TemplateRepository(db)
        self.policy = TicketPolicyService()

    async def upload_ticket_attachment(
        self,
        ticket_id: uuid.UUID,
        file: UploadFile,
        actor: ServiceDeskUser,
    ) -> ServiceDeskAttachment:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        self._ensure_mutable_ticket(ticket)
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
        self._ensure_mutable_ticket(ticket)
        if comment.author_user_id != actor.id and actor.access_type != ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Прикреплять файл к чужому комментарию может только автор или администратор Service Desk",
            )
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

    async def upload_field_attachment(
        self,
        ticket_id: uuid.UUID,
        field_key: str,
        file: UploadFile,
        actor: ServiceDeskUser,
    ) -> ServiceDeskAttachment:
        ticket = self._require_ticket(ticket_id)
        self._ensure_mutable_ticket(ticket)
        if ticket.status != ServiceDeskTicketStatus.DRAFT:
            raise HTTPException(status.HTTP_409_CONFLICT, "Файлы полей можно прикреплять только к черновику")
        if actor.id != ticket.requester_user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Прикреплять файлы полей может только заявитель")
        field = self.template_repository.get_field_by_key(ticket.template_version_id, field_key)
        if not field:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Поле формы не найдено")
        if field.field_type != TemplateFieldType.FILE:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Вложение доступно только для поля типа «Файл»")

        rules = field.validation or {}
        configured_limit = rules.get("max_files", settings.max_attachments_per_owner)
        try:
            max_files = min(int(configured_limit), settings.max_attachments_per_owner)
        except (TypeError, ValueError):
            max_files = settings.max_attachments_per_owner
        if max_files < 1:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Лимит файлов поля должен быть положительным")
        if self.repository.count_for_field_value(ticket.id, field.key) >= max_files:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Превышен лимит файлов поля")

        allowed_extensions = rules.get("allowed_extensions")
        return await self._store(
            owner_type=ServiceDeskAttachmentOwnerType.FIELD_VALUE,
            owner_id=ticket.id,
            ticket=ticket,
            file=file,
            actor=actor,
            comment_visibility=None,
            field_key=field.key,
            allowed_extensions=allowed_extensions if isinstance(allowed_extensions, list) else None,
        )

    def list_field_attachments(
        self,
        ticket_id: uuid.UUID,
        field_key: str,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskAttachment]:
        ticket = self._require_ticket(ticket_id)
        self.policy.require_view(ticket, actor)
        field = self.template_repository.get_field_by_key(ticket.template_version_id, field_key)
        if not field:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Поле формы не найдено")
        if field.field_type != TemplateFieldType.FILE:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Вложение доступно только для поля типа «Файл»")
        return self.repository.list_for_field_value(ticket.id, field.key)

    def field_value_payload(self, ticket_id: uuid.UUID) -> dict[str, list[dict[str, object]]]:
        result: dict[str, list[dict[str, object]]] = {}
        for attachment in self.repository.list_for_field_value(ticket_id):
            if not attachment.field_key:
                continue
            result.setdefault(attachment.field_key, []).append(
                {
                    "id": str(attachment.id),
                    "name": attachment.file_name,
                    "content_type": attachment.content_type,
                    "size_bytes": attachment.size_bytes,
                }
            )
        return result

    def get_downloadable_attachment(
        self,
        ticket_id: uuid.UUID,
        attachment_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> tuple[ServiceDeskAttachment, Path]:
        ticket = self._require_ticket(ticket_id)
        attachment = self.repository.get(attachment_id)
        if not attachment or attachment.ticket_id != ticket.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Вложение не найдено")
        self.policy.require_view(ticket, actor)

        if attachment.owner_type == ServiceDeskAttachmentOwnerType.COMMENT:
            comment = self.comment_repository.get_for_update(attachment.owner_id)
            if not comment or comment.ticket_id != ticket.id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Вложение не найдено")
            if comment.visibility == ServiceDeskCommentVisibility.INTERNAL:
                self.policy.require_internal_comments(ticket, actor)

        path = self._storage_path(attachment.storage_key)
        if not path.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Содержимое вложения не найдено")
        return attachment, path

    def delete_attachment(
        self,
        ticket_id: uuid.UUID,
        attachment_id: uuid.UUID,
        actor: ServiceDeskUser,
    ) -> None:
        ticket = self.ticket_repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        attachment = self.repository.get_for_update(attachment_id)
        if not attachment or attachment.ticket_id != ticket.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Вложение не найдено")

        is_admin = actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
        is_draft_owner = (
            ticket.status == ServiceDeskTicketStatus.DRAFT
            and ticket.requester_user_id == actor.id
        )
        if not (is_admin or is_draft_owner):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Удалить вложение может заявитель из своего черновика или администратор Service Desk",
            )

        path = self._storage_path(attachment.storage_key)
        tombstone = path.with_name(f".{path.name}.deleting-{uuid.uuid4().hex}")
        moved = False
        try:
            if path.is_file():
                path.replace(tombstone)
                moved = True
            self.repository.delete(attachment)
            self.ticket_repository.add_history(
                ServiceDeskTicketHistory(
                    ticket_id=ticket.id,
                    event_type="attachment_removed",
                    actor_user_id=actor.id,
                    message="Вложение удалено",
                    payload={
                        "attachment_id": str(attachment.id),
                        "owner_type": attachment.owner_type.value,
                        "field_key": attachment.field_key,
                        "file_name": attachment.file_name,
                    },
                )
            )
            self.db.commit()
        except BaseException:
            self._rollback_best_effort()
            if moved and tombstone.is_file():
                tombstone.replace(path)
            raise
        if moved:
            self._remove_file_best_effort(tombstone)

    async def _store(
        self,
        *,
        owner_type: ServiceDeskAttachmentOwnerType,
        owner_id: uuid.UUID,
        ticket: ServiceDeskTicket,
        file: UploadFile,
        actor: ServiceDeskUser,
        comment_visibility: ServiceDeskCommentVisibility | None,
        field_key: str | None = None,
        allowed_extensions: list[object] | None = None,
        max_attachments: int | None = None,
    ) -> ServiceDeskAttachment:
        limit = max_attachments or settings.max_attachments_per_owner
        if self.repository.count_for_owner(owner_type, owner_id) >= limit:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Превышен лимит вложений")
        file_name, extension = self._validate_file_metadata(file)
        if allowed_extensions:
            normalized_extensions = {str(item).lower().lstrip(".") for item in allowed_extensions}
            if extension.lstrip(".") not in normalized_extensions:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимое расширение файла для поля формы")
        storage_key = f"{owner_type.value}/{owner_id}/{uuid.uuid4().hex}{extension}"
        path = self._storage_path(storage_key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            size_bytes = await self._stream_upload(file, path)
            self._validate_file_content(path, extension)
            attachment = self.repository.add(
                ServiceDeskAttachment(
                    owner_type=owner_type,
                    owner_id=owner_id,
                    ticket_id=ticket.id,
                    field_key=field_key,
                    file_name=file_name,
                    storage_key=storage_key,
                    content_type=CONTENT_TYPE_BY_EXTENSION[extension],
                    size_bytes=size_bytes,
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
                        "field_key": field_key,
                        "file_name": file_name,
                        "comment_visibility": comment_visibility.value if comment_visibility else None,
                    },
                )
            )
            self.db.commit()
        except BaseException:
            self._rollback_best_effort()
            self._remove_file_best_effort(path)
            raise
        return attachment

    @staticmethod
    def _validate_file_metadata(file: UploadFile) -> tuple[str, str]:
        file_name = AttachmentService._sanitize_file_name(file.filename or "attachment")
        extension = Path(file_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимое расширение файла")
        declared_content_type = (file.content_type or "").partition(";")[0].strip().lower()
        if declared_content_type and declared_content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Недопустимый MIME-тип файла")
        if declared_content_type and declared_content_type != CONTENT_TYPE_BY_EXTENSION[extension]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "MIME-тип не соответствует расширению")
        return file_name, extension

    @staticmethod
    async def _stream_upload(file: UploadFile, path: Path) -> int:
        total_size = 0
        with path.open("xb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > settings.max_attachment_size_bytes:
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        "Файл превышает допустимый размер",
                    )
                destination.write(chunk)
        if total_size == 0:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Нельзя прикрепить пустой файл")
        return total_size

    @staticmethod
    def _validate_file_content(path: Path, extension: str) -> None:
        if extension == ".pdf":
            valid = AttachmentService._starts_with(path, b"%PDF-")
        elif extension in {".doc", ".xls", ".ppt"}:
            # Legacy Office formats share the OLE Compound File signature.
            valid = AttachmentService._starts_with(path, OLE_COMPOUND_FILE_SIGNATURE)
        elif extension == ".png":
            valid = AttachmentService._starts_with(path, b"\x89PNG\r\n\x1a\n")
        elif extension in {".jpg", ".jpeg"}:
            valid = AttachmentService._starts_with(path, b"\xff\xd8\xff")
        elif extension in {".txt", ".csv"}:
            valid = AttachmentService._is_utf8_text(path)
        elif extension in OOXML_MAIN_PART_BY_EXTENSION:
            valid = AttachmentService._is_valid_zip(
                path,
                required_parts={
                    "[Content_Types].xml",
                    "_rels/.rels",
                    OOXML_MAIN_PART_BY_EXTENSION[extension],
                },
            )
        elif extension == ".zip":
            valid = AttachmentService._is_valid_zip(path)
        else:  # pragma: no cover - guarded by the extension allowlist
            valid = False

        if not valid:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Содержимое файла не соответствует его расширению",
            )

    @staticmethod
    def _starts_with(path: Path, signature: bytes) -> bool:
        with path.open("rb") as source:
            return source.read(len(signature)) == signature

    @staticmethod
    def _is_utf8_text(path: Path) -> bool:
        decoder = codecs.getincrementaldecoder("utf-8")()
        try:
            with path.open("rb") as source:
                while chunk := source.read(UPLOAD_CHUNK_SIZE):
                    if b"\x00" in chunk:
                        return False
                    decoder.decode(chunk)
            decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            return False
        return True

    @staticmethod
    def _is_valid_zip(path: Path, required_parts: set[str] | None = None) -> bool:
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_ARCHIVE_ENTRIES:
                    return False
                names = {entry.filename for entry in entries}
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
            return False
        return not required_parts or required_parts.issubset(names)

    def _rollback_best_effort(self) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass

    @staticmethod
    def _remove_file_best_effort(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

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

    @staticmethod
    def _ensure_mutable_ticket(ticket: ServiceDeskTicket) -> None:
        if ticket.status in {ServiceDeskTicketStatus.CLOSED, ServiceDeskTicketStatus.CANCELLED}:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "В закрытую или отменённую заявку нельзя добавлять вложения",
            )
