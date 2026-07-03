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
)
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class ProjectResponseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectResponseRepository(db)

    def create_for_project(self, project_id: UUID, payload: ProjectResponseCreate) -> ProjectResponseRead:
        project = ProjectService(self.db).get_existing_project(project_id)
        if project.status not in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED} or project.archived_at is not None:
            raise DomainError("Отклики доступны только для активных и приостановленных проектов")

        email = ensure_utmn_email(payload.email)
        user = UserRepository(self.db).get_by_email(email)
        if user and user.role == UserRole.ADMIN:
            raise DomainError("Администратор не может отправлять отклики на проекты", status_code=403)
        response = self.repo.create(
            {
                **payload.model_dump(),
                "email": email,
                "project_id": project_id,
                "user_id": user.id if user else None,
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
        if response is None:
            raise DomainError("Отклик не найден", status_code=404)
        self._ensure_can_manage_project(response.project_id, current_user)
        response.status = status
        response.processed_by = current_user.id
        response.processed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(response)
        return self._to_admin_read(response)

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
