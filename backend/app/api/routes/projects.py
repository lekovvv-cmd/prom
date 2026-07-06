from typing import Literal
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.enums import ProjectStatus, ProjectType
from app.core.schemas.common import PaginatedResponse
from app.modules.projects.schemas import ProjectDetails, ProjectRecommendationRead, ProjectSummary
from app.modules.projects.service import ProjectService
from app.modules.responses.schemas import ProjectResponseCreate, ProjectResponseRead
from app.modules.responses.service import ProjectResponseService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectSummary])
def list_projects(
    db: DbSession,
    search: str | None = None,
    status: ProjectStatus | None = None,
    project_type: ProjectType | None = None,
    competency: str | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "priority_desc", "priority_asc"] = "created_at_desc",
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[ProjectSummary]:
    return ProjectService(db).list_public(
        search=search,
        status=status,
        project_type=project_type,
        competency=competency,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/recommendations", response_model=list[ProjectRecommendationRead])
def list_project_recommendations(
    current_user: CurrentUser,
    db: DbSession,
    limit: int | None = None,
) -> list[ProjectRecommendationRead]:
    return ProjectService(db).list_recommendations(current_user, limit=limit)


@router.get("/{project_id}", response_model=ProjectDetails)
def get_project(project_id: UUID, db: DbSession) -> ProjectDetails:
    return ProjectService(db).get_public_details(project_id)


@router.post("/{project_id}/responses", response_model=ProjectResponseRead, status_code=201)
def create_project_response(
    project_id: UUID,
    payload: ProjectResponseCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponseRead:
    return ProjectResponseService(db).create_for_project(project_id, payload, current_user=current_user)
