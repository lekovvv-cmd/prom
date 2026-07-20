from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Header

from app.api.deps import AdminUser, DbSession
from app.core.enums import ProjectResponseStatus, ProjectStatus, ProjectType
from app.core.http import parse_if_match
from app.core.schemas.common import PaginatedResponse
from app.modules.platform.idempotency import IdempotencyStore, request_fingerprint
from app.modules.projects.schemas import (
    OkResponse,
    ProjectCandidateRead,
    ProjectCreate,
    ProjectDetails,
    ProjectSummary,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.modules.responses.schemas import AdminProjectResponseRead
from app.modules.responses.service import ProjectResponseService

router = APIRouter(prefix="/admin/projects", tags=["admin-projects"])


@router.get("", response_model=PaginatedResponse[ProjectSummary])
def list_admin_projects(
    current_user: AdminUser,
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
        current_user=current_user,
    )


@router.post("", response_model=ProjectDetails, status_code=201)
def create_admin_project(
    payload: ProjectCreate,
    current_user: AdminUser,
    db: DbSession,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProjectDetails:
    scope = f"CreateProject:{current_user.id}"
    request_hash = request_fingerprint(payload.model_dump(mode="json"))
    store = IdempotencyStore(db)
    replay = store.replay(scope=scope, key=idempotency_key, request_hash=request_hash)
    if replay is not None:
        return ProjectDetails.model_validate(replay[1])
    result = ProjectService(db).create(payload, actor=current_user)
    store.save(
        scope=scope,
        key=idempotency_key,
        request_hash=request_hash,
        response_status=201,
        response_body=result.model_dump(mode="json"),
    )
    return result


@router.get("/{project_id}", response_model=ProjectDetails)
def get_admin_project(project_id: UUID, current_user: AdminUser, db: DbSession) -> ProjectDetails:
    return ProjectService(db).get_admin_details(project_id, current_user=current_user)


@router.patch("/{project_id}", response_model=ProjectDetails)
def update_admin_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: AdminUser,
    db: DbSession,
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> ProjectDetails:
    return ProjectService(db).update(
        project_id,
        payload,
        current_user=current_user,
        expected_version=parse_if_match(if_match),
    )


@router.delete("/{project_id}", response_model=OkResponse)
def archive_admin_project(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> OkResponse:
    ProjectService(db).archive(
        project_id,
        current_user=current_user,
        expected_version=parse_if_match(if_match),
    )
    return OkResponse(ok=True)


@router.patch("/{project_id}/restore", response_model=ProjectDetails)
def restore_admin_project(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> ProjectDetails:
    return ProjectService(db).restore(
        project_id,
        current_user=current_user,
        expected_version=parse_if_match(if_match),
    )


@router.get("/{project_id}/candidates", response_model=PaginatedResponse[ProjectCandidateRead])
def list_project_candidates(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    search: str | None = None,
    block_title: str | None = None,
    competency: str | None = None,
    sort: Literal["match_desc", "name_asc", "responses_asc"] = "match_desc",
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[ProjectCandidateRead]:
    return ProjectService(db).list_candidates(
        project_id=project_id,
        current_user=current_user,
        search=search,
        block_title=block_title,
        competency=competency,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.post("/{project_id}/members/{user_id}", response_model=ProjectDetails)
def add_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProjectDetails:
    scope = f"AddProjectMember:{project_id}:{current_user.id}"
    request_hash = request_fingerprint({"project_id": str(project_id), "user_id": str(user_id)})
    store = IdempotencyStore(db)
    replay = store.replay(scope=scope, key=idempotency_key, request_hash=request_hash)
    if replay is not None:
        return ProjectDetails.model_validate(replay[1])
    result = ProjectService(db).add_working_group_member(
        project_id=project_id,
        user_id=user_id,
        current_user=current_user,
    )
    store.save(
        scope=scope,
        key=idempotency_key,
        request_hash=request_hash,
        response_status=200,
        response_body=result.model_dump(mode="json"),
    )
    return result


@router.get("/{project_id}/responses", response_model=PaginatedResponse[AdminProjectResponseRead])
def list_project_responses(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    status: ProjectResponseStatus | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PaginatedResponse[AdminProjectResponseRead]:
    return ProjectResponseService(db).list_for_project(
        project_id=project_id,
        status=status,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
