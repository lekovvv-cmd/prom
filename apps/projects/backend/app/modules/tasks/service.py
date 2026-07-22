from datetime import date
from uuid import UUID

from platform_sdk.error_types import EntityNotFound, InvalidRequest, PermissionDenied
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectMemberRole, ProjectTaskStatus
from app.core.permissions import (
    PROJECTS_MANAGE_TASKS,
    can_manage_all_projects,
    can_manage_own_projects,
    has_permission,
)
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.platform.events import ProjectEventRecorder
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.query_service import ProjectQueryService
from app.modules.projects.service_base import ProjectServiceBase
from app.modules.tasks.models import ProjectStage, ProjectTask
from app.modules.tasks.repository import ProjectTaskRepository
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
from app.modules.tasks.workflows import ensure_task_transition
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserShort


class ProjectTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectTaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.events = ProjectEventRecorder(db)

    def list_admin_stages(self, project_id: UUID, current_user: User) -> list[ProjectStageWithTasksRead]:
        self._ensure_can_manage_project(project_id, current_user)
        stages = self.repo.list_stages(project_id)
        staged_task_ids = {task.id for stage in stages for task in stage.tasks}
        unassigned_stage = self._build_unassigned_stage(project_id, staged_task_ids)
        result = [self._to_stage_with_tasks(stage) for stage in stages]
        if unassigned_stage is not None:
            result.append(unassigned_stage)
        return result

    def create_stage(self, project_id: UUID, payload: ProjectStageCreate, current_user: User) -> ProjectStageRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._create_stage(project_id, payload, current_user)
            uow.commit()
            return result

    def _create_stage(self, project_id: UUID, payload: ProjectStageCreate, current_user: User) -> ProjectStageRead:
        self._ensure_can_manage_project(project_id, current_user)
        stage = self.repo.create_stage({"project_id": project_id, **payload.model_dump()})
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.stage_created",
            object_type="project_stage",
            object_id=stage.id,
            after={"project_id": str(project_id), "title": stage.title},
        )
        self.db.refresh(stage)
        return ProjectStageRead.model_validate(stage)

    def update_stage(
        self,
        project_id: UUID,
        stage_id: UUID,
        payload: ProjectStageUpdate,
        current_user: User,
    ) -> ProjectStageRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._update_stage(project_id, stage_id, payload, current_user)
            uow.commit()
            return result

    def _update_stage(
        self,
        project_id: UUID,
        stage_id: UUID,
        payload: ProjectStageUpdate,
        current_user: User,
    ) -> ProjectStageRead:
        self._ensure_can_manage_project(project_id, current_user)
        stage = self._get_stage(project_id, stage_id)
        before = {"title": stage.title, "position": stage.position}
        self.repo.update_stage(stage, payload.model_dump(exclude_unset=True))
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.stage_updated",
            object_type="project_stage",
            object_id=stage.id,
            before=before,
            after={"title": stage.title, "position": stage.position},
        )
        self.db.refresh(stage)
        return ProjectStageRead.model_validate(stage)

    def create_task(self, project_id: UUID, payload: ProjectTaskCreate, current_user: User) -> ProjectTaskRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._create_task(project_id, payload, current_user)
            uow.commit()
            return result

    def _create_task(self, project_id: UUID, payload: ProjectTaskCreate, current_user: User) -> ProjectTaskRead:
        self._ensure_can_manage_project(project_id, current_user)
        data = payload.model_dump()
        self._validate_task_links(project_id, data.get("stage_id"), data.get("assignee_user_id"))
        task = self.repo.create_task({"project_id": project_id, **data})
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.task_created",
            object_type="project_task",
            object_id=task.id,
            after=self._audit_snapshot(task),
        )
        if task.assignee_user_id is not None:
            self.events.publish(
                event_type="ProjectTaskAssigned",
                aggregate_type="project_task",
                aggregate_id=task.id,
                payload={
                    "task_id": str(task.id),
                    "project_id": str(project_id),
                    "assignee_user_id": str(task.assignee_user_id),
                },
            )
        self.db.refresh(task)
        return self._to_task_read(task)

    def update_task(
        self,
        project_id: UUID,
        task_id: UUID,
        payload: ProjectTaskUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._update_task(project_id, task_id, payload, current_user)
            uow.commit()
            return result

    def _update_task(
        self,
        project_id: UUID,
        task_id: UUID,
        payload: ProjectTaskUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        self._ensure_can_manage_project(project_id, current_user)
        task = self._get_task(project_id, task_id)
        before = self._audit_snapshot(task)
        data = payload.model_dump(exclude_unset=True)
        self._validate_task_links(project_id, data.get("stage_id"), data.get("assignee_user_id"))
        if (target_status := data.get("status")) is not None:
            ensure_task_transition(task.status, target_status)
        self.repo.update_task(task, data)
        self.db.flush()
        after = self._audit_snapshot(task)
        self.events.audit(
            actor=current_user,
            action="project.task_updated",
            object_type="project_task",
            object_id=task.id,
            before=before,
            after=after,
        )
        if before["assignee_user_id"] != after["assignee_user_id"] and task.assignee_user_id is not None:
            self.events.publish(
                event_type="ProjectTaskAssigned",
                aggregate_type="project_task",
                aggregate_id=task.id,
                payload={
                    "task_id": str(task.id),
                    "project_id": str(project_id),
                    "assignee_user_id": str(task.assignee_user_id),
                },
            )
        self.db.refresh(task)
        return self._to_task_read(task)

    def list_current_user_tasks(self, project_id: UUID, current_user: User) -> list[ProjectTaskRead]:
        ProjectQueryService(self.db).get_current_user_project_details(project_id, current_user)
        tasks = self.repo.list_assigned_tasks(project_id, current_user.id)
        return [self._to_task_read(task) for task in tasks]

    def update_current_user_task(
        self,
        task_id: UUID,
        payload: ProjectTaskStatusUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._update_current_user_task(task_id, payload, current_user)
            uow.commit()
            return result

    def _update_current_user_task(
        self,
        task_id: UUID,
        payload: ProjectTaskStatusUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        task = self.repo.get_task(task_id)
        if task is None:
            raise EntityNotFound("Задача не найдена")
        if task.assignee_user_id != current_user.id:
            raise PermissionDenied("Можно менять статус только своих задач")
        before = self._audit_snapshot(task)
        ensure_task_transition(task.status, payload.status)
        task.status = payload.status
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.task_status_changed",
            object_type="project_task",
            object_id=task.id,
            before=before,
            after=self._audit_snapshot(task),
        )
        self.db.refresh(task)
        return self._to_task_read(task)

    def ensure_can_attach_result(self, task_id: UUID, current_user: User) -> ProjectTask:
        task = self.repo.get_task(task_id)
        if task is None:
            raise EntityNotFound("Задача не найдена")
        if can_manage_all_projects(current_user) or (
            can_manage_own_projects(current_user)
            and has_permission(current_user, PROJECTS_MANAGE_TASKS)
            and self.project_repo.user_can_manage_project(task.project_id, current_user.id)
        ):
            return task
        if task.assignee_user_id == current_user.id:
            return task
        raise PermissionDenied("Недостаточно прав для загрузки результата к этой задаче")

    def _build_unassigned_stage(
        self,
        project_id: UUID,
        staged_task_ids: set[UUID],
    ) -> ProjectStageWithTasksRead | None:
        tasks = [task for task in self.repo.list_project_tasks(project_id) if task.id not in staged_task_ids]
        if not tasks:
            return None
        now = tasks[0].created_at
        return ProjectStageWithTasksRead(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            project_id=project_id,
            title="Без этапа",
            position=9999,
            start_date=None,
            end_date=None,
            created_at=now,
            updated_at=now,
            tasks=[self._to_task_read(task) for task in tasks],
        )

    def _ensure_can_manage_project(self, project_id: UUID, current_user: User) -> None:
        ProjectServiceBase(self.db).get_existing_project(project_id)
        if can_manage_all_projects(current_user):
            return
        if (
            not can_manage_own_projects(current_user)
            or not has_permission(current_user, PROJECTS_MANAGE_TASKS)
            or not self.project_repo.user_can_manage_project(project_id, current_user.id)
        ):
            raise PermissionDenied("Недостаточно прав для управления задачами этого проекта")

    def _get_stage(self, project_id: UUID, stage_id: UUID) -> ProjectStage:
        stage = self.repo.get_stage(stage_id)
        if stage is None or stage.project_id != project_id:
            raise EntityNotFound("Этап не найден")
        return stage

    def _get_task(self, project_id: UUID, task_id: UUID) -> ProjectTask:
        task = self.repo.get_task(task_id)
        if task is None or task.project_id != project_id:
            raise EntityNotFound("Задача не найдена")
        return task

    def _validate_task_links(
        self,
        project_id: UUID,
        stage_id: UUID | None,
        assignee_user_id: UUID | None,
    ) -> None:
        if stage_id is not None:
            self._get_stage(project_id, stage_id)
        if assignee_user_id is not None:
            user = UserRepository(self.db).get_by_id(assignee_user_id)
            if user is None:
                raise EntityNotFound("Исполнитель не найден")
            project, _ = self.project_repo.get_with_counts(project_id) or (None, 0)
            if project is None:
                raise EntityNotFound("Проект не найден")
            allowed_user_ids = {
                member.user_id
                for member in project.members
                if member.member_role == ProjectMemberRole.WORKING_GROUP_MEMBER
            }
            allowed_user_ids.update(user_id for user_id in (project.responsible_user_id, project.created_by) if user_id)
            if assignee_user_id not in allowed_user_ids:
                raise InvalidRequest("Исполнителя можно выбрать только из рабочей группы проекта")

    def _to_stage_with_tasks(self, stage: ProjectStage) -> ProjectStageWithTasksRead:
        return ProjectStageWithTasksRead(
            **ProjectStageRead.model_validate(stage).model_dump(),
            tasks=[self._to_task_read(task) for task in sorted(stage.tasks, key=lambda item: item.created_at)],
        )

    def _to_task_read(self, task: ProjectTask) -> ProjectTaskRead:
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.TASK, task.id)
        return ProjectTaskRead(
            id=task.id,
            project_id=task.project_id,
            stage_id=task.stage_id,
            title=task.title,
            description=task.description,
            assignee=UserShort.model_validate(task.assignee) if task.assignee else None,
            status=task.status,
            due_date=task.due_date,
            is_overdue=self._is_overdue(task),
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
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    def _is_overdue(task: ProjectTask) -> bool:
        return task.due_date is not None and task.due_date < date.today() and task.status not in {
            ProjectTaskStatus.DONE,
            ProjectTaskStatus.CANCELLED,
        }

    @staticmethod
    def _audit_snapshot(task: ProjectTask) -> dict[str, str | None]:
        return {
            "project_id": str(task.project_id),
            "stage_id": str(task.stage_id) if task.stage_id else None,
            "assignee_user_id": (
                str(task.assignee_user_id) if task.assignee_user_id else None
            ),
            "status": task.status.value,
        }
