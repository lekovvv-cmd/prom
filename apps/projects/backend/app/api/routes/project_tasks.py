from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.modules.tasks.schemas import (
    ProjectStageCreate,
    ProjectStageRead,
    ProjectStageUpdate,
    ProjectStageWithTasksRead,
    ProjectTaskCreate,
    ProjectTaskRead,
    ProjectTaskStatusUpdate,
    ProjectTaskUpdate,
)
from app.modules.tasks.service import ProjectTaskService

router = APIRouter(tags=["project-tasks"])


@router.get("/admin/projects/{project_id}/stages", response_model=list[ProjectStageWithTasksRead])
def list_admin_project_stages(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
) -> list[ProjectStageWithTasksRead]:
    return ProjectTaskService(db).list_admin_stages(project_id, current_user)


@router.post("/admin/projects/{project_id}/stages", response_model=ProjectStageRead, status_code=201)
def create_admin_project_stage(
    project_id: UUID,
    payload: ProjectStageCreate,
    current_user: AdminUser,
    db: DbSession,
) -> ProjectStageRead:
    return ProjectTaskService(db).create_stage(project_id, payload, current_user)


@router.patch("/admin/projects/{project_id}/stages/{stage_id}", response_model=ProjectStageRead)
def update_admin_project_stage(
    project_id: UUID,
    stage_id: UUID,
    payload: ProjectStageUpdate,
    current_user: AdminUser,
    db: DbSession,
) -> ProjectStageRead:
    return ProjectTaskService(db).update_stage(project_id, stage_id, payload, current_user)


@router.post("/admin/projects/{project_id}/tasks", response_model=ProjectTaskRead, status_code=201)
def create_admin_project_task(
    project_id: UUID,
    payload: ProjectTaskCreate,
    current_user: AdminUser,
    db: DbSession,
) -> ProjectTaskRead:
    return ProjectTaskService(db).create_task(project_id, payload, current_user)


@router.patch("/admin/projects/{project_id}/tasks/{task_id}", response_model=ProjectTaskRead)
def update_admin_project_task(
    project_id: UUID,
    task_id: UUID,
    payload: ProjectTaskUpdate,
    current_user: AdminUser,
    db: DbSession,
) -> ProjectTaskRead:
    return ProjectTaskService(db).update_task(project_id, task_id, payload, current_user)


@router.get("/me/projects/{project_id}/tasks", response_model=list[ProjectTaskRead])
def list_my_project_tasks(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[ProjectTaskRead]:
    return ProjectTaskService(db).list_current_user_tasks(project_id, current_user)


@router.patch("/me/project-tasks/{task_id}", response_model=ProjectTaskRead)
def update_my_project_task_status(
    task_id: UUID,
    payload: ProjectTaskStatusUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectTaskRead:
    return ProjectTaskService(db).update_current_user_task(task_id, payload, current_user)
