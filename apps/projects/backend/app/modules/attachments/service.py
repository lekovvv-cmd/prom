from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO

from platform_sdk.error_types import EntityNotFound, PermissionDenied, ValidationFailed
from platform_sdk.storage import IncomingFile, LocalFilesystemStorage, stream_incoming_file
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AttachmentOwnerType, AttachmentStatus, ProjectStatus
from app.core.permissions import (
    PROJECTS_MANAGE_REPORTS,
    can_manage_all_projects,
    can_manage_own_projects,
    has_permission,
)
from app.modules.attachments.models import Attachment
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.attachments.storage import antivirus_scanner, object_storage
from app.modules.attachments.validation import detect_and_validate, validate_metadata
from app.modules.platform.events import ProjectEventRecorder
from app.modules.projects.repository import ProjectRepository
from app.modules.reports.repository import ReportRepository
from app.modules.responses.repository import ProjectResponseRepository
from app.modules.tasks.repository import ProjectTaskRepository
from app.modules.users.models import User


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttachmentRepository(db)
        self.projects = ProjectRepository(db)
        self.responses = ProjectResponseRepository(db)
        self.tasks = ProjectTaskRepository(db)
        self.reports = ReportRepository(db)
        self.events = ProjectEventRecorder(db)
        self.storage = object_storage()
        self.scanner = antivirus_scanner()

    async def upload_project_file(
        self,
        project_id: uuid.UUID,
        file: IncomingFile,
        *,
        actor: User,
    ) -> AttachmentRead:
        self._require_manage_project(project_id, actor)
        return await self._upload(
            owner_type=AttachmentOwnerType.PROJECT,
            owner_id=project_id,
            file=file,
            actor=actor,
        )

    async def upload_response_file(
        self,
        project_id: uuid.UUID,
        response_id: uuid.UUID,
        file: IncomingFile,
        *,
        current_user: User,
    ) -> AttachmentRead:
        response = self.responses.get_by_id(response_id)
        if response is None or response.project_id != project_id:
            raise EntityNotFound("Отклик не найден")
        if response.user_id != current_user.id:
            self._require_manage_project(project_id, current_user)
        return await self._upload(
            owner_type=AttachmentOwnerType.RESPONSE,
            owner_id=response_id,
            file=file,
            actor=current_user,
        )

    async def upload_task_file(
        self,
        task_id: uuid.UUID,
        file: IncomingFile,
        *,
        current_user: User,
    ) -> AttachmentRead:
        task = self.tasks.get_task(task_id)
        if task is None:
            raise EntityNotFound("Задача не найдена")
        if task.assignee_user_id != current_user.id:
            self._require_manage_project(task.project_id, current_user)
        return await self._upload(
            owner_type=AttachmentOwnerType.TASK,
            owner_id=task_id,
            file=file,
            actor=current_user,
        )

    async def upload_stage_file(
        self,
        project_id: uuid.UUID,
        stage_id: uuid.UUID,
        file: IncomingFile,
        *,
        current_user: User,
    ) -> AttachmentRead:
        stage = self.tasks.get_stage(stage_id)
        if stage is None or stage.project_id != project_id:
            raise EntityNotFound("Этап не найден")
        self._require_manage_project(project_id, current_user)
        return await self._upload(
            owner_type=AttachmentOwnerType.STAGE,
            owner_id=stage_id,
            file=file,
            actor=current_user,
        )

    async def upload_report_file(
        self,
        report_id: uuid.UUID,
        file: IncomingFile,
        *,
        current_user: User,
    ) -> AttachmentRead:
        report = self.reports.get_report(report_id)
        if report is None:
            raise EntityNotFound("Отчёт не найден")
        if report.user_id != current_user.id and not (
            can_manage_all_projects(current_user)
            or has_permission(current_user, PROJECTS_MANAGE_REPORTS)
        ):
            raise PermissionDenied("Недостаточно прав для вложений этого отчёта")
        return await self._upload(
            owner_type=AttachmentOwnerType.REPORT,
            owner_id=report_id,
            file=file,
            actor=current_user,
        )

    def list_project_files(self, project_id: uuid.UUID) -> list[AttachmentRead]:
        return self._to_read_many(
            self.repo.list_for_owner(AttachmentOwnerType.PROJECT, project_id)
        )

    def list_response_files(self, response_id: uuid.UUID) -> list[AttachmentRead]:
        return self._to_read_many(
            self.repo.list_for_owner(AttachmentOwnerType.RESPONSE, response_id)
        )

    def list_task_files(self, task_id: uuid.UUID) -> list[AttachmentRead]:
        return self._to_read_many(
            self.repo.list_for_owner(AttachmentOwnerType.TASK, task_id)
        )

    def get_download(
        self,
        attachment_id: uuid.UUID,
        *,
        current_user: User,
    ) -> tuple[Attachment, BinaryIO]:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._get_download(attachment_id, current_user=current_user)
            uow.commit()
            return result

    def _get_download(
        self,
        attachment_id: uuid.UUID,
        *,
        current_user: User,
    ) -> tuple[Attachment, BinaryIO]:
        attachment = self.repo.get_by_id(attachment_id)
        if attachment is None or attachment.status != AttachmentStatus.AVAILABLE:
            raise EntityNotFound("Файл не найден")
        self._require_view_attachment(attachment, current_user)
        storage_key = attachment.storage_key
        if not storage_key:
            legacy_path = Path(attachment.storage_path)
            if not legacy_path.is_file():
                raise EntityNotFound("Файл не найден в хранилище")
            source = legacy_path.open("rb")
        else:
            if not self.storage.exists(storage_key):
                raise EntityNotFound("Файл не найден в хранилище")
            source = self.storage.get(storage_key)
        self.events.audit(
            actor=current_user,
            action="project.attachment_downloaded",
            object_type="attachment",
            object_id=attachment.id,
            after={
                "owner_type": attachment.owner_type.value,
                "owner_id": str(attachment.owner_id),
                "checksum": attachment.checksum,
            },
        )
        return attachment, source

    def delete_attachment(
        self,
        attachment_id: uuid.UUID,
        *,
        current_user: User,
    ) -> None:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            self._request_attachment_deletion(
                attachment_id,
                current_user=current_user,
            )
            uow.commit()

    def _request_attachment_deletion(
        self,
        attachment_id: uuid.UUID,
        *,
        current_user: User,
    ) -> None:
        attachment = self.repo.get_by_id(attachment_id)
        if attachment is None:
            raise EntityNotFound("Файл не найден")
        if attachment.uploaded_by != current_user.id:
            self._require_manage_attachment_owner(attachment, current_user)
        before = self._audit_snapshot(attachment)
        attachment.status = AttachmentStatus.PENDING_DELETE
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.attachment_deleted",
            object_type="attachment",
            object_id=attachment.id,
            before=before,
            after=self._audit_snapshot(attachment),
        )
        self.events.publish(
            event_type="AttachmentDeletionRequested",
            aggregate_type="attachment",
            aggregate_id=attachment.id,
            payload={
                "attachment_id": str(attachment.id),
                "storage_key": attachment.storage_key,
                "storage_path": attachment.storage_path,
            },
        )

    async def _upload(
        self,
        *,
        owner_type: AttachmentOwnerType,
        owner_id: uuid.UUID,
        file: IncomingFile,
        actor: User,
    ) -> AttachmentRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = await self._stage_upload(
                owner_type=owner_type,
                owner_id=owner_id,
                file=file,
                actor=actor,
            )
            attachment = self.repo.get_by_id(result.id)
            try:
                uow.commit()
            except BaseException:
                if attachment is not None and attachment.storage_key:
                    self.storage.delete(attachment.storage_key)
                raise
            return result

    async def _stage_upload(
        self,
        *,
        owner_type: AttachmentOwnerType,
        owner_id: uuid.UUID,
        file: IncomingFile,
        actor: User,
    ) -> AttachmentRead:
        if self.repo.count_for_owner(owner_type, owner_id) >= settings.max_attachments_per_owner:
            raise ValidationFailed("Превышен лимит вложений для объекта")

        safe_name, extension, declared_type = validate_metadata(file)
        storage_key = (
            f"{owner_type.value}/{owner_id}/{uuid.uuid4().hex}{extension}"
        )
        quarantine = (
            Path(settings.uploads_dir)
            / ".quarantine"
            / f"{uuid.uuid4().hex}{extension}"
        ).resolve()
        stored = False
        try:
            streamed = await stream_incoming_file(
                file,
                destination=quarantine,
                max_size_bytes=settings.max_attachment_size_bytes,
            )
            detected_type = detect_and_validate(quarantine, extension)
            attachment = self.repo.create(
                {
                    "module": "projects",
                    "owner_type": owner_type,
                    "owner_id": owner_id,
                    "file_name": safe_name,
                    "storage_path": storage_key,
                    "content_type": detected_type,
                    "storage_key": storage_key,
                    "original_name": Path(file.file_name or safe_name).name[:255],
                    "safe_name": safe_name,
                    "content_type_declared": declared_type,
                    "content_type_detected": detected_type,
                    "checksum": streamed.checksum,
                    "status": AttachmentStatus.QUARANTINED,
                    "size_bytes": streamed.size_bytes,
                    "uploaded_by": actor.id,
                }
            )
            scan_result = self.scanner.scan(quarantine)
            if scan_result != "clean":
                attachment.status = AttachmentStatus.REJECTED
                self.db.flush()
                raise ValidationFailed("Файл отклонён антивирусной проверкой")
            with quarantine.open("rb") as source:
                checksum = self.storage.put(storage_key, source)
            stored = True
            if checksum != streamed.checksum:
                raise RuntimeError("Storage checksum mismatch")
            if isinstance(self.storage, LocalFilesystemStorage):
                attachment.storage_path = str(self.storage.path_for(storage_key))
            attachment.status = AttachmentStatus.AVAILABLE
            self.db.flush()
            self.events.audit(
                actor=actor,
                action="project.attachment_uploaded",
                object_type="attachment",
                object_id=attachment.id,
                after=self._audit_snapshot(attachment),
            )
            return self._to_read(attachment)
        except ValueError as exc:
            if stored:
                self.storage.delete(storage_key)
            raise ValidationFailed(str(exc)) from exc
        except BaseException:
            if stored:
                self.storage.delete(storage_key)
            raise
        finally:
            quarantine.unlink(missing_ok=True)

    def _require_view_attachment(self, attachment: Attachment, actor: User) -> None:
        if attachment.owner_type == AttachmentOwnerType.PROJECT:
            self._require_view_project(attachment.owner_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.RESPONSE:
            response = self.responses.get_by_id(attachment.owner_id)
            if response is None:
                raise EntityNotFound("Отклик не найден")
            if response.user_id == actor.id:
                return
            self._require_manage_project(response.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.TASK:
            task = self.tasks.get_task(attachment.owner_id)
            if task is None:
                raise EntityNotFound("Задача не найдена")
            if task.assignee_user_id == actor.id:
                return
            self._require_view_project(task.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.STAGE:
            stage = self.tasks.get_stage(attachment.owner_id)
            if stage is None:
                raise EntityNotFound("Этап не найден")
            self._require_view_project(stage.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.REPORT:
            report = self.reports.get_report(attachment.owner_id)
            if report is None:
                raise EntityNotFound("Отчёт не найден")
            if report.user_id == actor.id:
                return
            if can_manage_all_projects(actor) or has_permission(
                actor,
                PROJECTS_MANAGE_REPORTS,
            ):
                return
            raise PermissionDenied("Недостаточно прав для скачивания отчёта")
        raise PermissionDenied("Неподдерживаемый владелец вложения")

    def _require_manage_attachment_owner(
        self,
        attachment: Attachment,
        actor: User,
    ) -> None:
        if attachment.owner_type == AttachmentOwnerType.PROJECT:
            self._require_manage_project(attachment.owner_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.RESPONSE:
            response = self.responses.get_by_id(attachment.owner_id)
            if response is None:
                raise EntityNotFound("Отклик не найден")
            self._require_manage_project(response.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.TASK:
            task = self.tasks.get_task(attachment.owner_id)
            if task is None:
                raise EntityNotFound("Задача не найдена")
            self._require_manage_project(task.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.STAGE:
            stage = self.tasks.get_stage(attachment.owner_id)
            if stage is None:
                raise EntityNotFound("Этап не найден")
            self._require_manage_project(stage.project_id, actor)
            return
        if attachment.owner_type == AttachmentOwnerType.REPORT:
            if can_manage_all_projects(actor) or has_permission(
                actor,
                PROJECTS_MANAGE_REPORTS,
            ):
                return
        raise PermissionDenied("Недостаточно прав для удаления вложения")

    def _require_view_project(self, project_id: uuid.UUID, actor: User) -> None:
        project = self.projects.get_by_id(project_id)
        if project is None or project.deleted_at is not None:
            raise EntityNotFound("Проект не найден")
        if (
            project.status not in {ProjectStatus.DRAFT, ProjectStatus.ARCHIVED}
            and project.archived_at is None
        ):
            return
        if can_manage_all_projects(actor):
            return
        if self.projects.user_can_view_project(project_id, actor.id, actor.email):
            return
        if (
            can_manage_own_projects(actor)
            and self.projects.user_can_manage_project(project_id, actor.id)
        ):
            return
        raise PermissionDenied("Недостаточно прав для просмотра вложения проекта")

    def _require_manage_project(self, project_id: uuid.UUID, actor: User) -> None:
        project = self.projects.get_by_id(project_id)
        if project is None or project.deleted_at is not None:
            raise EntityNotFound("Проект не найден")
        if can_manage_all_projects(actor):
            return
        if (
            can_manage_own_projects(actor)
            and self.projects.user_can_manage_project(project_id, actor.id)
        ):
            return
        raise PermissionDenied("Недостаточно прав для управления вложениями проекта")

    def _to_read_many(self, attachments: list[Attachment]) -> list[AttachmentRead]:
        return [self._to_read(attachment) for attachment in attachments]

    @staticmethod
    def _to_read(attachment: Attachment) -> AttachmentRead:
        return AttachmentRead(
            id=attachment.id,
            owner_type=attachment.owner_type,
            owner_id=attachment.owner_id,
            file_name=attachment.safe_name or attachment.file_name,
            content_type=attachment.content_type_detected or attachment.content_type,
            content_type_detected=attachment.content_type_detected,
            size_bytes=attachment.size_bytes,
            checksum=attachment.checksum,
            status=attachment.status,
            download_url=f"/api/attachments/{attachment.id}",
            created_at=attachment.created_at,
        )

    @staticmethod
    def _audit_snapshot(attachment: Attachment) -> dict[str, str | int | None]:
        return {
            "owner_type": attachment.owner_type.value,
            "owner_id": str(attachment.owner_id),
            "safe_name": attachment.safe_name or attachment.file_name,
            "content_type": attachment.content_type_detected or attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "checksum": attachment.checksum,
            "status": attachment.status.value,
        }
