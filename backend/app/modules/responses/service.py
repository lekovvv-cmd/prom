from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import ProjectResponseStatus, ProjectStatus
from app.core.exceptions import DomainError
from app.core.schemas.common import PaginatedResponse
from app.core.security import ensure_utmn_email
from app.modules.projects.service import ProjectService
from app.modules.responses.models import ProjectResponse
from app.modules.responses.repository import ProjectResponseRepository
from app.modules.responses.schemas import (
    AdminProjectResponseRead,
    ProjectResponseCreate,
    ProjectResponseRead,
)
from app.modules.users.repository import UserRepository


class ProjectResponseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectResponseRepository(db)

    def create_for_project(self, project_id: UUID, payload: ProjectResponseCreate) -> ProjectResponseRead:
        project = ProjectService(self.db).get_existing_project(project_id)
        if project.status in {ProjectStatus.DRAFT, ProjectStatus.ARCHIVED} or project.archived_at is not None:
            raise DomainError("Нельзя откликнуться на черновик или архивный проект")

        email = ensure_utmn_email(payload.email)
        user = UserRepository(self.db).get_by_email(email)
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
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        items, total, safe_limit, safe_offset = self.repo.list_responses(
            project_id=project_id,
            status=status,
            search=search,
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
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        ProjectService(self.db).get_existing_project(project_id)
        items, total, safe_limit, safe_offset = self.repo.list_project_responses(
            project_id=project_id,
            status=status,
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
        processed_by: UUID,
    ) -> AdminProjectResponseRead:
        response = self.repo.get_by_id(response_id)
        if response is None:
            raise DomainError("Отклик не найден", status_code=404)
        response.status = status
        response.processed_by = processed_by
        response.processed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(response)
        return self._to_admin_read(response)

    @staticmethod
    def _to_admin_read(response: ProjectResponse) -> AdminProjectResponseRead:
        return AdminProjectResponseRead(
            id=response.id,
            project_id=response.project_id,
            project_title=response.project.title,
            full_name=response.full_name,
            email=response.email,
            comment=response.comment,
            competencies=response.competencies,
            status=response.status,
            created_at=response.created_at,
            processed_by=response.processed_by,
            processed_at=response.processed_at,
        )
