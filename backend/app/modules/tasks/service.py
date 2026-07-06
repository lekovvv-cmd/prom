from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectMemberRole, ProjectTaskStatus, UserRole
from app.core.exceptions import DomainError
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.service import ProjectService
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
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserShort


class ProjectTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectTaskRepository(db)
        self.project_repo = ProjectRepository(db)

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
        self._ensure_can_manage_project(project_id, current_user)
        stage = self.repo.create_stage({"project_id": project_id, **payload.model_dump()})
        self.db.commit()
        self.db.refresh(stage)
        return ProjectStageRead.model_validate(stage)

    def update_stage(
        self,
        project_id: UUID,
        stage_id: UUID,
        payload: ProjectStageUpdate,
        current_user: User,
    ) -> ProjectStageRead:
        self._ensure_can_manage_project(project_id, current_user)
        stage = self._get_stage(project_id, stage_id)
        self.repo.update_stage(stage, payload.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(stage)
        return ProjectStageRead.model_validate(stage)

    def create_task(self, project_id: UUID, payload: ProjectTaskCreate, current_user: User) -> ProjectTaskRead:
        self._ensure_can_manage_project(project_id, current_user)
        data = payload.model_dump()
        self._validate_task_links(project_id, data.get("stage_id"), data.get("assignee_user_id"))
        task = self.repo.create_task({"project_id": project_id, **data})
        self.db.commit()
        self.db.refresh(task)
        return self._to_task_read(task)

    def update_task(
        self,
        project_id: UUID,
        task_id: UUID,
        payload: ProjectTaskUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        self._ensure_can_manage_project(project_id, current_user)
        task = self._get_task(project_id, task_id)
        data = payload.model_dump(exclude_unset=True)
        self._validate_task_links(project_id, data.get("stage_id"), data.get("assignee_user_id"))
        self.repo.update_task(task, data)
        self.db.commit()
        self.db.refresh(task)
        return self._to_task_read(task)

    def list_current_user_tasks(self, project_id: UUID, current_user: User) -> list[ProjectTaskRead]:
        ProjectService(self.db).get_current_user_project_details(project_id, current_user)
        tasks = self.repo.list_assigned_tasks(project_id, current_user.id)
        return [self._to_task_read(task) for task in tasks]

    def update_current_user_task(
        self,
        task_id: UUID,
        payload: ProjectTaskStatusUpdate,
        current_user: User,
    ) -> ProjectTaskRead:
        task = self.repo.get_task(task_id)
        if task is None:
            raise DomainError("Задача не найдена", status_code=404)
        if task.assignee_user_id != current_user.id:
            raise DomainError("Можно менять статус только своих задач", status_code=403)
        task.status = payload.status
        self.db.commit()
        self.db.refresh(task)
        return self._to_task_read(task)

    def ensure_can_attach_result(self, task_id: UUID, current_user: User) -> ProjectTask:
        task = self.repo.get_task(task_id)
        if task is None:
            raise DomainError("Задача не найдена", status_code=404)
        if current_user.role == UserRole.ADMIN or self.project_repo.user_can_manage_project(task.project_id, current_user.id):
            return task
        if task.assignee_user_id == current_user.id:
            return task
        raise DomainError("Недостаточно прав для загрузки результата к этой задаче", status_code=403)

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
        ProjectService(self.db).get_existing_project(project_id)
        if current_user.role == UserRole.ADMIN:
            return
        if not self.project_repo.user_can_manage_project(project_id, current_user.id):
            raise DomainError("Недостаточно прав для управления задачами этого проекта", status_code=403)

    def _get_stage(self, project_id: UUID, stage_id: UUID) -> ProjectStage:
        stage = self.repo.get_stage(stage_id)
        if stage is None or stage.project_id != project_id:
            raise DomainError("Этап не найден", status_code=404)
        return stage

    def _get_task(self, project_id: UUID, task_id: UUID) -> ProjectTask:
        task = self.repo.get_task(task_id)
        if task is None or task.project_id != project_id:
            raise DomainError("Задача не найдена", status_code=404)
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
                raise DomainError("Исполнитель не найден", status_code=404)
            project, _ = self.project_repo.get_with_counts(project_id) or (None, 0)
            if project is None:
                raise DomainError("Проект не найден", status_code=404)
            allowed_user_ids = {
                member.user_id
                for member in project.members
                if member.member_role == ProjectMemberRole.WORKING_GROUP_MEMBER
            }
            allowed_user_ids.update(user_id for user_id in (project.responsible_user_id, project.created_by) if user_id)
            if assignee_user_id not in allowed_user_ids:
                raise DomainError("Исполнителя можно выбрать только из рабочей группы проекта")

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
