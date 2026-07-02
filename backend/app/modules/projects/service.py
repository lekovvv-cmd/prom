from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectStatus, ProjectType
from app.core.exceptions import DomainError
from app.core.schemas.common import PaginatedResponse
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectDetails,
    ProjectMemberRead,
    ProjectSummary,
    ProjectUpdate,
)
from app.modules.users.schemas import UserShort


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

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
    ) -> PaginatedResponse[ProjectSummary]:
        return self._list(
            public=False,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def get_public_details(self, project_id: UUID) -> ProjectDetails:
        project, count = self._get_existing_with_count(project_id)
        if project.status in {ProjectStatus.DRAFT, ProjectStatus.ARCHIVED} or project.archived_at is not None:
            raise DomainError("Проект не найден", status_code=404)
        return self._to_details(project, count)

    def get_admin_details(self, project_id: UUID) -> ProjectDetails:
        project, count = self._get_existing_with_count(project_id)
        return self._to_details(project, count)

    def get_existing_project(self, project_id: UUID) -> Project:
        project = self.repo.get_by_id(project_id)
        if project is None:
            raise DomainError("Проект не найден", status_code=404)
        return project

    def create(self, payload: ProjectCreate, created_by: UUID) -> ProjectDetails:
        project = self.repo.create(data=payload.model_dump(), created_by=created_by)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def update(self, project_id: UUID, payload: ProjectUpdate) -> ProjectDetails:
        project = self.get_existing_project(project_id)
        data = payload.model_dump(exclude_unset=True)
        self.repo.update(project, data)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def archive(self, project_id: UUID) -> None:
        project = self.get_existing_project(project_id)
        self.repo.archive(project)
        self.db.commit()

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
    ) -> PaginatedResponse[ProjectSummary]:
        rows, total, safe_limit, safe_offset = self.repo.list_projects(
            public=public,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_summary(project, count) for project, count in rows],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def _get_existing_with_count(self, project_id: UUID) -> tuple[Project, int]:
        row = self.repo.get_with_counts(project_id)
        if row is None:
            raise DomainError("Проект не найден", status_code=404)
        return row

    @staticmethod
    def _to_summary(project: Project, responses_count: int) -> ProjectSummary:
        return ProjectSummary(
            id=project.id,
            title=project.title,
            short_description=project.short_description,
            goal=project.goal,
            project_type=project.project_type,
            priority=project.priority,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            responsible=UserShort.model_validate(project.responsible) if project.responsible else None,
            required_competencies=project.required_competencies,
            responses_count=responses_count,
            created_at=project.created_at,
        )

    def _to_details(self, project: Project, responses_count: int) -> ProjectDetails:
        summary = self._to_summary(project, responses_count).model_dump()
        members = [
            ProjectMemberRead(
                id=member.user.id,
                full_name=member.user.full_name,
                email=member.user.email,
                member_role=member.member_role,
            )
            for member in project.members
        ]
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.PROJECT, project.id)
        return ProjectDetails(
            **summary,
            description=project.description,
            expected_result=project.expected_result,
            contact_email=project.contact_email,
            members=members,
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
            planned_tasks=project.planned_tasks,
            updated_at=project.updated_at,
        )
