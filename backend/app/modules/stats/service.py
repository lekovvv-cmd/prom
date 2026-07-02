from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import ProjectResponseStatus, ProjectStatus
from app.modules.projects.models import Project
from app.modules.responses.models import ProjectResponse
from app.modules.stats.schemas import AdminStats, ResponsesByProject


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_admin_stats(self) -> AdminStats:
        projects_total = self.db.scalar(select(func.count(Project.id))) or 0
        projects_active = self.db.scalar(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
        ) or 0
        projects_archived = self.db.scalar(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.ARCHIVED)
        ) or 0
        responses_total = self.db.scalar(select(func.count(ProjectResponse.id))) or 0
        responses_new = self._count_response_status(ProjectResponseStatus.NEW)
        responses_accepted = self._count_response_status(ProjectResponseStatus.ACCEPTED)
        responses_rejected = self._count_response_status(ProjectResponseStatus.REJECTED)

        rows = self.db.execute(
            select(Project.id, Project.title, func.count(ProjectResponse.id))
            .outerjoin(ProjectResponse, Project.id == ProjectResponse.project_id)
            .group_by(Project.id, Project.title)
            .order_by(func.count(ProjectResponse.id).desc(), Project.title.asc())
        )
        responses_by_project = [
            ResponsesByProject(project_id=project_id, project_title=title, responses_count=int(count))
            for project_id, title, count in rows
        ]
        return AdminStats(
            projects_total=projects_total,
            projects_active=projects_active,
            projects_archived=projects_archived,
            responses_total=responses_total,
            responses_new=responses_new,
            responses_accepted=responses_accepted,
            responses_rejected=responses_rejected,
            responses_by_project=responses_by_project,
        )

    def _count_response_status(self, status: ProjectResponseStatus) -> int:
        return self.db.scalar(select(func.count(ProjectResponse.id)).where(ProjectResponse.status == status)) or 0
