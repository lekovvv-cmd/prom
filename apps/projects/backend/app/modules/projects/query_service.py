from __future__ import annotations

from uuid import UUID

from platform_sdk.error_types import EntityNotFound, PermissionDenied

from app.core.enums import ProjectStatus, ProjectType
from app.core.schemas.common import PaginatedResponse
from app.modules.projects.schemas import ProjectDetails, ProjectSummary
from app.modules.projects.service_base import ProjectServiceBase
from app.modules.users.models import User


class ProjectQueryService(ProjectServiceBase):
    def list_public(
        self,
        *,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectSummary]:
        return self._list(
            public=True,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def list_admin(
        self,
        *,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
        current_user: User | None = None,
    ) -> PaginatedResponse[ProjectSummary]:
        return self._list(
            public=False,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            manager_user_id=self.manager_scope_user_id(current_user),
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def list_current_user_projects(
        self,
        *,
        current_user: User,
        search: str | None,
        status: ProjectStatus | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectSummary]:
        rows, total, safe_limit, safe_offset = self.repo.list_user_projects(
            user_id=current_user.id,
            email=current_user.email,
            search=search,
            status=status,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self.to_summary(project, count) for project, count in rows],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def get_public_details(self, project_id: UUID) -> ProjectDetails:
        project, count = self.get_existing_with_count(project_id)
        if (
            project.status in {ProjectStatus.DRAFT, ProjectStatus.ARCHIVED}
            or project.archived_at is not None
            or project.deleted_at is not None
        ):
            raise EntityNotFound("Проект не найден")
        return self.to_details(project, count)

    def get_admin_details(
        self,
        project_id: UUID,
        current_user: User | None = None,
    ) -> ProjectDetails:
        self.ensure_can_manage_project(project_id, current_user)
        project, count = self.get_existing_with_count(project_id)
        return self.to_details(project, count)

    def get_current_user_project_details(
        self,
        project_id: UUID,
        current_user: User,
    ) -> ProjectDetails:
        project, count = self.get_existing_with_count(project_id)
        if not self.repo.user_can_view_project(project_id, current_user.id, current_user.email):
            raise PermissionDenied("Недостаточно прав для просмотра этого проекта")
        return self.to_details(project, count)

    def _list(
        self,
        *,
        public: bool,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
        manager_user_id: UUID | None = None,
    ) -> PaginatedResponse[ProjectSummary]:
        rows, total, safe_limit, safe_offset = self.repo.list_projects(
            public=public,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            manager_user_id=manager_user_id,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self.to_summary(project, count) for project, count in rows],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )
