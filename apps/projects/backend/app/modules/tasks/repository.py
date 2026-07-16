from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.tasks.models import ProjectStage, ProjectTask


class ProjectTaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_stage(self, data: dict) -> ProjectStage:
        stage = ProjectStage(**data)
        self.db.add(stage)
        self.db.flush()
        return stage

    def update_stage(self, stage: ProjectStage, data: dict) -> ProjectStage:
        for key, value in data.items():
            setattr(stage, key, value)
        self.db.flush()
        return stage

    def get_stage(self, stage_id: UUID) -> ProjectStage | None:
        return self.db.get(ProjectStage, stage_id)

    def list_stages(self, project_id: UUID) -> list[ProjectStage]:
        query = (
            select(ProjectStage)
            .where(ProjectStage.project_id == project_id)
            .options(selectinload(ProjectStage.tasks).selectinload(ProjectTask.assignee))
            .order_by(ProjectStage.position.asc(), ProjectStage.created_at.asc())
        )
        return list(self.db.scalars(query))

    def create_task(self, data: dict) -> ProjectTask:
        task = ProjectTask(**data)
        self.db.add(task)
        self.db.flush()
        return task

    def update_task(self, task: ProjectTask, data: dict) -> ProjectTask:
        for key, value in data.items():
            setattr(task, key, value)
        self.db.flush()
        return task

    def get_task(self, task_id: UUID) -> ProjectTask | None:
        query = (
            select(ProjectTask)
            .where(ProjectTask.id == task_id)
            .options(selectinload(ProjectTask.assignee), selectinload(ProjectTask.stage))
        )
        return self.db.scalar(query)

    def list_project_tasks(self, project_id: UUID) -> list[ProjectTask]:
        query = (
            select(ProjectTask)
            .where(ProjectTask.project_id == project_id)
            .options(selectinload(ProjectTask.assignee), selectinload(ProjectTask.stage))
            .order_by(ProjectTask.created_at.asc())
        )
        return list(self.db.scalars(query))

    def list_assigned_tasks(self, project_id: UUID, assignee_user_id: UUID) -> list[ProjectTask]:
        query = (
            select(ProjectTask)
            .where(ProjectTask.project_id == project_id, ProjectTask.assignee_user_id == assignee_user_id)
            .options(selectinload(ProjectTask.assignee), selectinload(ProjectTask.stage))
            .order_by(ProjectTask.due_date.asc().nulls_last(), ProjectTask.created_at.asc())
        )
        return list(self.db.scalars(query))
