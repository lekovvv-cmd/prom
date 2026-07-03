from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AttachmentOwnerType, UserRole
from app.core.exceptions import DomainError
from app.modules.attachments.models import Attachment
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.projects.service import ProjectService
from app.modules.responses.repository import ProjectResponseRepository
from app.modules.users.models import User


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttachmentRepository(db)

    def upload_project_file(self, project_id: UUID, file: UploadFile, uploaded_by: UUID | None) -> AttachmentRead:
        ProjectService(self.db).get_existing_project(project_id)
        return self._upload(
            owner_type=AttachmentOwnerType.PROJECT,
            owner_id=project_id,
            file=file,
            uploaded_by=uploaded_by,
        )

    def upload_response_file(
        self,
        project_id: UUID,
        response_id: UUID,
        file: UploadFile,
        *,
        current_user: User,
    ) -> AttachmentRead:
        response = ProjectResponseRepository(self.db).get_by_id(response_id)
        if response is None or response.project_id != project_id:
            raise DomainError("Отклик не найден", status_code=404)
        if current_user.role != UserRole.ADMIN and response.user_id != current_user.id:
            raise DomainError("Недостаточно прав для загрузки файла к этому отклику", status_code=403)
        return self._upload(
            owner_type=AttachmentOwnerType.RESPONSE,
            owner_id=response_id,
            file=file,
            uploaded_by=current_user.id,
        )

    def list_project_files(self, project_id: UUID) -> list[AttachmentRead]:
        return self._to_read_many(self.repo.list_for_owner(AttachmentOwnerType.PROJECT, project_id))

    def list_response_files(self, response_id: UUID) -> list[AttachmentRead]:
        return self._to_read_many(self.repo.list_for_owner(AttachmentOwnerType.RESPONSE, response_id))

    def get_download(self, attachment_id: UUID) -> FileResponse:
        attachment = self.repo.get_by_id(attachment_id)
        if attachment is None:
            raise DomainError("Файл не найден", status_code=404)

        path = Path(attachment.storage_path)
        if not path.exists() or not path.is_file():
            raise DomainError("Файл не найден на диске", status_code=404)

        return FileResponse(
            path,
            media_type=attachment.content_type or "application/octet-stream",
            filename=attachment.file_name,
        )

    def _upload(
        self,
        *,
        owner_type: AttachmentOwnerType,
        owner_id: UUID,
        file: UploadFile,
        uploaded_by: UUID | None,
    ) -> AttachmentRead:
        safe_name = self._sanitize_filename(file.filename or "attachment")
        payload = file.file.read()
        if not payload:
            raise DomainError("Файл пустой")
        if len(payload) > 10 * 1024 * 1024:
            raise DomainError("Файл больше 10 МБ")

        directory = Path(settings.uploads_dir) / owner_type.value / str(owner_id)
        directory.mkdir(parents=True, exist_ok=True)
        storage_path = directory / f"{uuid4()}_{safe_name}"
        storage_path.write_bytes(payload)

        attachment = self.repo.create(
            {
                "owner_type": owner_type,
                "owner_id": owner_id,
                "file_name": safe_name,
                "storage_path": str(storage_path),
                "content_type": file.content_type,
                "size_bytes": len(payload),
                "uploaded_by": uploaded_by,
            }
        )
        self.db.commit()
        self.db.refresh(attachment)
        return self._to_read(attachment)

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        cleaned = file_name.replace("\\", "_").replace("/", "_").strip()
        return cleaned[:255] or "attachment"

    def _to_read_many(self, attachments: list[Attachment]) -> list[AttachmentRead]:
        return [self._to_read(attachment) for attachment in attachments]

    @staticmethod
    def _to_read(attachment: Attachment) -> AttachmentRead:
        return AttachmentRead(
            id=attachment.id,
            owner_type=attachment.owner_type,
            owner_id=attachment.owner_id,
            file_name=attachment.file_name,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            download_url=f"/api/attachments/{attachment.id}",
            created_at=attachment.created_at,
        )
