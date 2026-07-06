from datetime import UTC, datetime
import re
from uuid import UUID

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ProjectMemberRole, ProjectPriority, ProjectResponseStatus, ProjectStatus, ProjectType
from app.core.pagination import clamp_limit, clamp_offset
from app.modules.projects.models import Project, ProjectMember
from app.modules.responses.models import ProjectResponse


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_projects(
        self,
        *,
        public: bool,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        manager_user_id: UUID | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> tuple[list[tuple[Project, int]], int, int, int]:
        safe_limit = clamp_limit(limit)
        safe_offset = clamp_offset(offset)
        base = select(Project)
        base = self._apply_filters(base, public, search, status, project_type, competency, manager_user_id)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        response_counts = (
            select(
                ProjectResponse.project_id.label("project_id"),
                func.count(ProjectResponse.id).label("responses_count"),
            )
            .where(ProjectResponse.deleted_at.is_(None))
            .group_by(ProjectResponse.project_id)
            .subquery()
        )
        priority_rank = case(
            (Project.priority == ProjectPriority.CRITICAL, 4),
            (Project.priority == ProjectPriority.HIGH, 3),
            (Project.priority == ProjectPriority.MEDIUM, 2),
            else_=1,
        )
        query = (
            select(Project, func.coalesce(response_counts.c.responses_count, 0))
            .outerjoin(response_counts, Project.id == response_counts.c.project_id)
            .options(selectinload(Project.responsible))
        )
        query = self._apply_filters(query, public, search, status, project_type, competency, manager_user_id)
        if sort == "created_at_asc":
            query = query.order_by(Project.created_at.asc())
        elif sort == "priority_asc":
            query = query.order_by(priority_rank.asc(), Project.created_at.desc())
        elif sort == "priority_desc":
            query = query.order_by(priority_rank.desc(), Project.created_at.desc())
        else:
            query = query.order_by(Project.created_at.desc())

        rows = self.db.execute(query.limit(safe_limit).offset(safe_offset)).all()
        return [(project, int(count)) for project, count in rows], total, safe_limit, safe_offset

    def list_user_projects(
        self,
        *,
        user_id: UUID,
        email: str,
        search: str | None,
        status: ProjectStatus | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> tuple[list[tuple[Project, int]], int, int, int]:
        safe_limit = clamp_limit(limit)
        safe_offset = clamp_offset(offset)
        base = select(Project).where(Project.deleted_at.is_(None))
        base = self._apply_user_project_scope(base, user_id, email)
        base = self._apply_search_and_status(base, search, status)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        response_counts = (
            select(
                ProjectResponse.project_id.label("project_id"),
                func.count(ProjectResponse.id).label("responses_count"),
            )
            .where(ProjectResponse.deleted_at.is_(None))
            .group_by(ProjectResponse.project_id)
            .subquery()
        )
        priority_rank = self._priority_rank()
        query = (
            select(Project, func.coalesce(response_counts.c.responses_count, 0))
            .outerjoin(response_counts, Project.id == response_counts.c.project_id)
            .options(selectinload(Project.responsible))
            .where(Project.deleted_at.is_(None))
        )
        query = self._apply_user_project_scope(query, user_id, email)
        query = self._apply_search_and_status(query, search, status)
        query = self._apply_sort(query, sort, priority_rank)

        rows = self.db.execute(query.limit(safe_limit).offset(safe_offset)).all()
        return [(project, int(count)) for project, count in rows], total, safe_limit, safe_offset

    def get_with_counts(self, project_id: UUID) -> tuple[Project, int] | None:
        response_count = (
            select(func.count(ProjectResponse.id))
            .where(ProjectResponse.project_id == project_id, ProjectResponse.deleted_at.is_(None))
            .scalar_subquery()
        )
        query = (
            select(Project, response_count)
            .where(Project.id == project_id)
            .options(selectinload(Project.responsible), selectinload(Project.members).selectinload(ProjectMember.user))
        )
        row = self.db.execute(query).one_or_none()
        if row is None:
            return None
        project, count = row
        return project, int(count)

    def get_by_id(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def user_can_manage_project(self, project_id: UUID, user_id: UUID) -> bool:
        query = select(Project.id).where(Project.id == project_id, Project.deleted_at.is_(None))
        query = self._apply_manager_project_scope(query, user_id)
        return self.db.scalar(query) is not None

    def user_can_view_project(self, project_id: UUID, user_id: UUID, email: str) -> bool:
        query = select(Project.id).where(Project.id == project_id, Project.deleted_at.is_(None))
        query = self._apply_user_project_scope(query, user_id, email)
        return self.db.scalar(query) is not None

    def list_accepted_response_competencies(self, project_id: UUID) -> list[str | None]:
        query = select(ProjectResponse.competencies).where(
            ProjectResponse.project_id == project_id,
            ProjectResponse.status == ProjectResponseStatus.ACCEPTED,
            ProjectResponse.deleted_at.is_(None),
        )
        return list(self.db.scalars(query))

    def list_project_response_user_ids(self, project_id: UUID) -> set[UUID]:
        query = select(ProjectResponse.user_id).where(
            ProjectResponse.project_id == project_id,
            ProjectResponse.user_id.is_not(None),
            ProjectResponse.status != ProjectResponseStatus.CANCELLED,
            ProjectResponse.deleted_at.is_(None),
        )
        return {user_id for user_id in self.db.scalars(query) if user_id is not None}

    def list_user_response_project_ids(self, user_id: UUID, email: str) -> set[UUID]:
        query = select(ProjectResponse.project_id).where(
            ProjectResponse.deleted_at.is_(None),
            ProjectResponse.status != ProjectResponseStatus.CANCELLED,
            or_(ProjectResponse.user_id == user_id, func.lower(ProjectResponse.email) == email.lower()),
        )
        return {project_id for project_id in self.db.scalars(query)}

    def create(self, *, data: dict, created_by: UUID) -> Project:
        project = Project(**data, created_by=created_by)
        self.db.add(project)
        self.db.flush()
        return project

    def update(self, project: Project, data: dict) -> Project:
        for key, value in data.items():
            setattr(project, key, value)
        if project.status == ProjectStatus.ARCHIVED and project.archived_at is None:
            project.archived_at = datetime.now(UTC)
        if project.status != ProjectStatus.ARCHIVED:
            project.archived_at = None
            project.deleted_at = None
        self.db.flush()
        return project

    def replace_working_group(self, project: Project, user_ids: list[UUID]) -> None:
        project.members[:] = [
            member for member in project.members if member.member_role != ProjectMemberRole.WORKING_GROUP_MEMBER
        ]
        self.db.flush()
        project.members.extend(
            ProjectMember(
                user_id=user_id,
                member_role=ProjectMemberRole.WORKING_GROUP_MEMBER,
            )
            for user_id in user_ids
        )
        self.db.flush()

    def add_working_group_member(self, project: Project, user_id: UUID) -> None:
        if any(member.user_id == user_id for member in project.members):
            return
        project.members.append(
            ProjectMember(
                user_id=user_id,
                member_role=ProjectMemberRole.WORKING_GROUP_MEMBER,
            )
        )
        self.db.flush()

    def archive(self, project: Project) -> None:
        project.status = ProjectStatus.ARCHIVED
        project.archived_at = datetime.now(UTC)
        self.db.flush()

    def soft_delete(self, project: Project) -> None:
        project.status = ProjectStatus.ARCHIVED
        if project.archived_at is None:
            project.archived_at = datetime.now(UTC)
        project.deleted_at = datetime.now(UTC)
        self.db.flush()

    def restore_from_archive(self, project: Project) -> None:
        project.status = ProjectStatus.ACTIVE
        project.archived_at = None
        project.deleted_at = None
        self.db.flush()

    @staticmethod
    def _apply_filters(
        query: Select,
        public: bool,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        manager_user_id: UUID | None,
    ) -> Select:
        query = query.where(Project.deleted_at.is_(None))
        if public:
            query = query.where(Project.status.notin_([ProjectStatus.DRAFT, ProjectStatus.ARCHIVED]))
            query = query.where(Project.archived_at.is_(None))
        elif status is None:
            query = query.where(Project.status != ProjectStatus.ARCHIVED)
            query = query.where(Project.archived_at.is_(None))
        if manager_user_id is not None:
            query = ProjectRepository._apply_manager_project_scope(query, manager_user_id)
        search_terms = ProjectRepository._split_search_terms(search)
        for term in search_terms:
            pattern = f"%{term}%"
            query = query.where(
                or_(
                    Project.title.ilike(pattern),
                    Project.short_description.ilike(pattern),
                    Project.goal.ilike(pattern),
                    Project.required_competencies.ilike(pattern),
                )
            )
        if status is not None:
            query = query.where(Project.status == status)
        if project_type is not None:
            query = query.where(Project.project_type == project_type)
        if competency:
            competencies = ProjectRepository._split_competency_filter(competency)
            if competencies:
                query = query.where(
                    or_(
                        *(
                            Project.required_competencies.ilike(f"%{item}%")
                            for item in competencies
                        )
                    )
                )
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

    @staticmethod
    def _apply_user_project_scope(query: Select, user_id: UUID, email: str) -> Select:
        member_exists = (
            select(ProjectMember.id)
            .where(ProjectMember.project_id == Project.id, ProjectMember.user_id == user_id)
            .exists()
        )
        accepted_response_exists = (
            select(ProjectResponse.id)
            .where(
                ProjectResponse.project_id == Project.id,
                ProjectResponse.deleted_at.is_(None),
                ProjectResponse.status == ProjectResponseStatus.ACCEPTED,
                or_(ProjectResponse.user_id == user_id, func.lower(ProjectResponse.email) == email.lower()),
            )
            .exists()
        )
        return query.where(or_(member_exists, accepted_response_exists))

    @staticmethod
    def _apply_search_and_status(
        query: Select,
        search: str | None,
        status: ProjectStatus | None,
    ) -> Select:
        search_terms = ProjectRepository._split_search_terms(search)
        for term in search_terms:
            pattern = f"%{term}%"
            query = query.where(
                or_(
                    Project.title.ilike(pattern),
                    Project.short_description.ilike(pattern),
                    Project.goal.ilike(pattern),
                    Project.required_competencies.ilike(pattern),
                )
            )
        if status is not None:
            query = query.where(Project.status == status)
        return query

    @staticmethod
    def _priority_rank():
        return case(
            (Project.priority == ProjectPriority.CRITICAL, 4),
            (Project.priority == ProjectPriority.HIGH, 3),
            (Project.priority == ProjectPriority.MEDIUM, 2),
            else_=1,
        )

    @staticmethod
    def _apply_sort(query: Select, sort: str, priority_rank) -> Select:
        if sort == "created_at_asc":
            return query.order_by(Project.created_at.asc())
        if sort == "priority_asc":
            return query.order_by(priority_rank.asc(), Project.created_at.desc())
        if sort == "priority_desc":
            return query.order_by(priority_rank.desc(), Project.created_at.desc())
        return query.order_by(Project.created_at.desc())

    @staticmethod
    def _split_competency_filter(value: str) -> list[str]:
        return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]

    @staticmethod
    def _split_search_terms(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in re.split(r"\s+", value) if item.strip()]
