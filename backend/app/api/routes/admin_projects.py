from typing import Literal
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.core.enums import ProjectResponseStatus, ProjectStatus, ProjectType
from app.core.schemas.common import PaginatedResponse
from app.modules.projects.schemas import OkResponse, ProjectCreate, ProjectDetails, ProjectSummary, ProjectUpdate
from app.modules.projects.service import ProjectService
from app.modules.responses.schemas import AdminProjectResponseRead
from app.modules.responses.service import ProjectResponseService

router = APIRouter(prefix="/admin/projects", tags=["admin-projects"])


@router.get("", response_model=PaginatedResponse[ProjectSummary])
def list_admin_projects(
    _: AdminUser,
    db: DbSession,
    search: str | None = None,
    status: ProjectStatus | None = None,
    project_type: ProjectType | None = None,
    competency: str | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "priority_desc", "priority_asc"] = "created_at_desc",
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[ProjectSummary]:
    return ProjectService(db).list_admin(
        search=search,
        status=status,
        project_type=project_type,
        competency=competency,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProjectDetails, status_code=201)
def create_admin_project(
    payload: ProjectCreate,
    current_user: AdminUser,
    db: DbSession,
) -> ProjectDetails:
    return ProjectService(db).create(payload, created_by=current_user.id)


@router.get("/{project_id}", response_model=ProjectDetails)
def get_admin_project(project_id: UUID, _: AdminUser, db: DbSession) -> ProjectDetails:
    return ProjectService(db).get_admin_details(project_id)


@router.patch("/{project_id}", response_model=ProjectDetails)
def update_admin_project(
    project_id: UUID,
    payload: ProjectUpdate,
    _: AdminUser,
    db: DbSession,
) -> ProjectDetails:
    return ProjectService(db).update(project_id, payload)


@router.delete("/{project_id}", response_model=OkResponse)
def archive_admin_project(project_id: UUID, _: AdminUser, db: DbSession) -> OkResponse:
    ProjectService(db).archive(project_id)
    return OkResponse(ok=True)


@router.get("/{project_id}/responses", response_model=PaginatedResponse[AdminProjectResponseRead])
def list_project_responses(
    project_id: UUID,
    _: AdminUser,
    db: DbSession,
    status: ProjectResponseStatus | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[AdminProjectResponseRead]:
    return ProjectResponseService(db).list_for_project(
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )
