from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ProjectMemberRole, ProjectResponseStatus
from app.core.pagination import clamp_limit, clamp_offset
from app.modules.projects.models import Project, ProjectMember
from app.modules.responses.models import ProjectResponse


class ProjectResponseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict) -> ProjectResponse:
        response = ProjectResponse(**data)
        self.db.add(response)
        self.db.flush()
        return response

    def get_by_id(self, response_id: UUID) -> ProjectResponse | None:
        return self.db.get(ProjectResponse, response_id)

    def exists_for_project_email(self, project_id: UUID, email: str) -> bool:
        query = (
            select(ProjectResponse.id)
            .where(ProjectResponse.project_id == project_id)
            .where(func.lower(ProjectResponse.email) == email.lower())
            .limit(1)
        )
        return self.db.scalar(query) is not None

    def list_responses(
        self,
        *,
        project_id: UUID | None,
        status: ProjectResponseStatus | None,
        search: str | None,
        manager_user_id: UUID | None,
        limit: int | None,
        offset: int | None,
    ) -> tuple[list[ProjectResponse], int, int, int]:
        safe_limit = clamp_limit(limit)
        safe_offset = clamp_offset(offset)
        base = select(ProjectResponse).join(Project)
        base = self._apply_filters(base, project_id, status, search, manager_user_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        query = (
            select(ProjectResponse)
            .join(Project)
            .options(selectinload(ProjectResponse.project))
            .order_by(ProjectResponse.created_at.desc())
        )
        query = self._apply_filters(query, project_id, status, search, manager_user_id)
        items = list(self.db.scalars(query.limit(safe_limit).offset(safe_offset)))
        return items, total, safe_limit, safe_offset

    def list_project_responses(
        self,
        *,
        project_id: UUID,
        status: ProjectResponseStatus | None,
        manager_user_id: UUID | None,
        limit: int | None,
        offset: int | None,
    ) -> tuple[list[ProjectResponse], int, int, int]:
        return self.list_responses(
            project_id=project_id,
            status=status,
            search=None,
            manager_user_id=manager_user_id,
            limit=limit,
            offset=offset,
        )

    def user_can_manage_project(self, project_id: UUID, user_id: UUID) -> bool:
        query = select(Project.id).where(Project.id == project_id, Project.deleted_at.is_(None))
        query = self._apply_manager_project_scope(query, user_id)
        return self.db.scalar(query) is not None

    @staticmethod
    def _apply_filters(
        query: Select,
        project_id: UUID | None,
        status: ProjectResponseStatus | None,
        search: str | None,
        manager_user_id: UUID | None,
    ) -> Select:
        query = query.where(Project.deleted_at.is_(None))
        if project_id is not None:
            query = query.where(ProjectResponse.project_id == project_id)
        if manager_user_id is not None:
            query = ProjectResponseRepository._apply_manager_project_scope(query, manager_user_id)
        if status is not None:
            query = query.where(ProjectResponse.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(or_(ProjectResponse.full_name.ilike(pattern), ProjectResponse.email.ilike(pattern)))
        return query

    @staticmethod
    def _apply_manager_project_scope(query: Select, manager_user_id: UUID) -> Select:
        manager_member_exists = (
            select(ProjectMember.id).where(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == manager_user_id,
                ProjectMember.member_role == ProjectMemberRole.MANAGER,
            )
        ).exists()
        return query.where(
            or_(
                Project.responsible_user_id == manager_user_id,
                Project.created_by == manager_user_id,
                manager_member_exists,
            )
        )
