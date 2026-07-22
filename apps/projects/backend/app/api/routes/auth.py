from typing import Literal
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.enums import ProjectStatus
from app.core.schemas.common import PaginatedResponse
from app.modules.projects.schemas import ProjectDetails, ProjectSummary
from app.modules.projects.query_service import ProjectQueryService
from app.modules.responses.schemas import UserProjectResponseRead
from app.modules.responses.service import ProjectResponseService
from app.modules.users.schemas import UserProfileUpdate, UserRead
from app.modules.users.service import UserService

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me/profile", response_model=UserRead)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserRead:
    return UserRead.model_validate(UserService(db).update_profile(current_user, payload))


@router.get("/me/projects", response_model=PaginatedResponse[ProjectSummary])
def list_my_projects(
    current_user: CurrentUser,
    db: DbSession,
    search: str | None = None,
    status: ProjectStatus | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "priority_desc", "priority_asc"] = "created_at_desc",
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[ProjectSummary]:
    return ProjectQueryService(db).list_current_user_projects(
        current_user=current_user,
        search=search,
        status=status,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/me/projects/{project_id}", response_model=ProjectDetails)
def get_my_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectDetails:
    return ProjectQueryService(db).get_current_user_project_details(
        project_id=project_id,
        current_user=current_user,
    )


@router.get("/me/responses", response_model=PaginatedResponse[UserProjectResponseRead])
def list_my_responses(
    current_user: CurrentUser,
    db: DbSession,
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[UserProjectResponseRead]:
    return ProjectResponseService(db).list_current_user(
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.delete("/me/responses/{response_id}", response_model=UserProjectResponseRead)
def withdraw_my_response(
    response_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> UserProjectResponseRead:
    return ProjectResponseService(db).withdraw_current_user(response_id=response_id, current_user=current_user)
