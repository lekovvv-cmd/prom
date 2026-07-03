from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.core.enums import ProjectResponseStatus
from app.core.schemas.common import PaginatedResponse
from app.modules.responses.schemas import (
    AdminProjectResponseRead,
    ProjectResponseStatusUpdate,
)
from app.modules.responses.service import ProjectResponseService

router = APIRouter(prefix="/admin/responses", tags=["admin-responses"])


@router.get("", response_model=PaginatedResponse[AdminProjectResponseRead])
def list_admin_responses(
    current_user: AdminUser,
    db: DbSession,
    project_id: UUID | None = None,
    status: ProjectResponseStatus | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[AdminProjectResponseRead]:
    return ProjectResponseService(db).list_admin(
        project_id=project_id,
        status=status,
        search=search,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.patch("/{response_id}", response_model=AdminProjectResponseRead)
def update_response_status(
    response_id: UUID,
    payload: ProjectResponseStatusUpdate,
    current_user: AdminUser,
    db: DbSession,
) -> AdminProjectResponseRead:
    return ProjectResponseService(db).update_status(
        response_id=response_id,
        status=payload.status,
        current_user=current_user,
    )
