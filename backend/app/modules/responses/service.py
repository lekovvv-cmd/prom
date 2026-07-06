from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectResponseStatus, ProjectStatus, UserRole
from app.core.exceptions import DomainError
from app.core.schemas.common import PaginatedResponse
from app.core.security import ensure_utmn_email
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.projects.service import ProjectService
from app.modules.responses.models import ProjectResponse
from app.modules.responses.repository import ProjectResponseRepository
from app.modules.responses.schemas import (
    AdminProjectResponseRead,
    ProjectResponseCreate,
    ProjectResponseRead,
    UserProjectResponseRead,
)
from app.modules.users.models import User


class ProjectResponseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectResponseRepository(db)

    def create_for_project(
        self,
        project_id: UUID,
        payload: ProjectResponseCreate,
        *,
        current_user: User,
    ) -> ProjectResponseRead:
        project = ProjectService(self.db).get_existing_project(project_id)
        if project.status not in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED} or project.archived_at is not None:
            raise DomainError("Отклики доступны только для активных и приостановленных проектов")

        email = ensure_utmn_email(payload.email)
        if current_user.role == UserRole.ADMIN:
            raise DomainError("Администратор не может отправлять отклики на проекты", status_code=403)
        if email != current_user.email:
            raise DomainError("Отклик можно отправить только от своего email", status_code=403)
        if self.repo.exists_for_project_email(project_id, email):
            raise DomainError("Вы уже откликнулись на этот проект", status_code=409)
        data = payload.model_dump()
        data["competencies"] = current_user.competencies
        response = self.repo.create(
            {
                **data,
                "email": email,
                "project_id": project_id,
                "user_id": current_user.id,
                "status": ProjectResponseStatus.NEW,
            }
        )
        self.db.commit()
        self.db.refresh(response)
        return ProjectResponseRead.model_validate(response)

    def list_admin(
        self,
        *,
        project_id: UUID | None,
        status: ProjectResponseStatus | None,
        search: str | None,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        items, total, safe_limit, safe_offset = self.repo.list_responses(
            project_id=project_id,
            status=status,
            search=search,
            manager_user_id=self._manager_scope_user_id(current_user),
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_admin_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def list_current_user(
        self,
        *,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[UserProjectResponseRead]:
        items, total, safe_limit, safe_offset = self.repo.list_user_responses(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_user_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def list_for_project(
        self,
        *,
        project_id: UUID,
        status: ProjectResponseStatus | None,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        ProjectService(self.db).get_existing_project(project_id)
        self._ensure_can_manage_project(project_id, current_user)
        items, total, safe_limit, safe_offset = self.repo.list_project_responses(
            project_id=project_id,
            status=status,
            manager_user_id=self._manager_scope_user_id(current_user),
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_admin_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def update_status(
        self,
        response_id: UUID,
        status: ProjectResponseStatus,
        current_user: User,
    ) -> AdminProjectResponseRead:
        response = self.repo.get_by_id(response_id)
        if response is None or response.deleted_at is not None:
            raise DomainError("Отклик не найден", status_code=404)
        self._ensure_can_manage_project(response.project_id, current_user)
        response.status = status
        response.processed_by = current_user.id
        response.processed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(response)
        return self._to_admin_read(response)

    def withdraw_current_user(self, response_id: UUID, current_user: User) -> UserProjectResponseRead:
        response = self.repo.get_user_response(response_id, current_user.id)
        if response is None:
            raise DomainError("Отклик не найден", status_code=404)
        if response.status in {ProjectResponseStatus.ACCEPTED, ProjectResponseStatus.REJECTED}:
            raise DomainError("Нельзя отозвать отклик после финального решения", status_code=400)
        response.status = ProjectResponseStatus.CANCELLED
        self.db.commit()
        self.db.refresh(response)
        return self._to_user_read(response)

    def delete_admin(self, response_id: UUID, current_user: User) -> None:
        response = self.repo.get_by_id(response_id)
        if response is None or response.deleted_at is not None:
            raise DomainError("Отклик не найден", status_code=404)
        self._ensure_can_manage_project(response.project_id, current_user)
        self.repo.soft_delete(response)
        self.db.commit()

    @staticmethod
    def _manager_scope_user_id(current_user: User) -> UUID | None:
        if current_user.role == UserRole.ADMIN:
            return None
        return current_user.id

    def _ensure_can_manage_project(self, project_id: UUID, current_user: User) -> None:
        if current_user.role == UserRole.ADMIN:
            return
        if not self.repo.user_can_manage_project(project_id, current_user.id):
            raise DomainError("Недостаточно прав для работы с откликами этого проекта", status_code=403)

    def _to_admin_read(self, response: ProjectResponse) -> AdminProjectResponseRead:
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.RESPONSE, response.id)
        return AdminProjectResponseRead(
            id=response.id,
            project_id=response.project_id,
            project_title=response.project.title,
            full_name=response.full_name,
            email=response.email,
            comment=response.comment,
            competencies=response.competencies,
            attachments=[
                AttachmentRead(
                    id=attachment.id,
                    owner_type=attachment.owner_type,
                    owner_id=attachment.owner_id,
                    file_name=attachment.file_name,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    download_url=f"/api/attachments/{attachment.id}",
                    created_at=attachment.created_at,
                )
                for attachment in attachments
            ],
            status=response.status,
            created_at=response.created_at,
            processed_by=response.processed_by,
            processed_at=response.processed_at,
        )

    def _to_user_read(self, response: ProjectResponse) -> UserProjectResponseRead:
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.RESPONSE, response.id)
        return UserProjectResponseRead(
            id=response.id,
            project_id=response.project_id,
            project_title=response.project.title,
            full_name=response.full_name,
            email=response.email,
            comment=response.comment,
            competencies=response.competencies,
            attachments=[
                AttachmentRead(
                    id=attachment.id,
                    owner_type=attachment.owner_type,
                    owner_id=attachment.owner_id,
                    file_name=attachment.file_name,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    download_url=f"/api/attachments/{attachment.id}",
                    created_at=attachment.created_at,
                )
                for attachment in attachments
            ],
            status=response.status,
            created_at=response.created_at,
        )
