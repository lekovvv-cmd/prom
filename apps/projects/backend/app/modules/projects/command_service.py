from __future__ import annotations

from uuid import UUID

from platform_sdk.error_types import ConflictDetected, InvalidRequest
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork

from app.core.enums import ProjectStatus
from app.modules.platform.events import project_snapshot
from app.modules.platform.idempotency import IdempotencyStore, request_fingerprint
from app.modules.projects.schemas import ProjectCreate, ProjectDetails, ProjectUpdate
from app.modules.projects.service_base import UNSET, ProjectServiceBase
from app.modules.projects.workflows import ensure_project_transition
from app.modules.users.models import User


class ProjectCommandService(ProjectServiceBase):
    def create(
        self,
        payload: ProjectCreate,
        actor: User,
        *,
        idempotency_key: str | None = None,
    ) -> ProjectDetails:
        scope = f"CreateProject:{actor.id}"
        request_hash = request_fingerprint(payload.model_dump(mode="json"))
        with SqlAlchemyUnitOfWork(self.db) as uow:
            store = IdempotencyStore(self.db)
            replay = store.replay(
                scope=scope,
                key=idempotency_key,
                request_hash=request_hash,
            )
            if replay is not None:
                uow.commit()
                return ProjectDetails.model_validate(replay[1])
            data = self.normalize_competency_data(payload.model_dump())
            member_ids = self.ensure_users_exist(
                data.pop("working_group_member_ids", [])
            )
            self.ensure_responsible_exists(payload.responsible_user_id)
            project = self.repo.create(data=data, created_by=actor.id)
            self.repo.replace_working_group(project, member_ids)
            self.events.audit(
                actor=actor,
                action="project.created",
                object_type="project",
                object_id=project.id,
                after=project_snapshot(project),
            )
            self.events.publish(
                event_type="ProjectCreated",
                aggregate_type="project",
                aggregate_id=project.id,
                payload={"project_id": str(project.id), "status": project.status.value},
            )
            if project.status == ProjectStatus.ACTIVE:
                self.events.publish(
                    event_type="ProjectPublished",
                    aggregate_type="project",
                    aggregate_id=project.id,
                    payload={"project_id": str(project.id), "version": project.version},
                )
            self.db.flush()
            project, count = self.get_existing_with_count(project.id)
            result = self.to_details(project, count)
            store.save(
                scope=scope,
                key=idempotency_key,
                request_hash=request_hash,
                response_status=201,
                response_body=result.model_dump(mode="json"),
            )
            uow.commit()
            return result

    def update(
        self,
        project_id: UUID,
        payload: ProjectUpdate,
        current_user: User | None = None,
        expected_version: int | None = None,
    ) -> ProjectDetails:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._update(
                project_id,
                payload,
                current_user=current_user,
                expected_version=expected_version,
            )
            uow.commit()
            return result

    def publish(
        self,
        project_id: UUID,
        current_user: User,
        expected_version: int | None = None,
    ) -> ProjectDetails:
        return self.update(
            project_id,
            ProjectUpdate(status=ProjectStatus.ACTIVE),
            current_user=current_user,
            expected_version=expected_version,
        )

    def _update(
        self,
        project_id: UUID,
        payload: ProjectUpdate,
        *,
        current_user: User | None,
        expected_version: int | None,
    ) -> ProjectDetails:
        self.ensure_can_manage_project(project_id, current_user)
        project = self.get_existing_project(project_id)
        before = project_snapshot(project)
        data = self.normalize_competency_data(payload.model_dump(exclude_unset=True))
        target_status = data.get("status")
        if target_status is not None:
            ensure_project_transition(project.status, target_status)
        if self.repo.claim_version(project, expected_version) != 1:
            raise ConflictDetected("Проект был изменён другим пользователем; обновите данные")
        member_ids = data.pop("working_group_member_ids", UNSET)
        self.ensure_responsible_exists(data.get("responsible_user_id"))
        if member_ids is not UNSET:
            self.repo.replace_working_group(
                project,
                self.ensure_users_exist(member_ids or []),
            )
        self.repo.update(project, data)
        self.db.flush()
        after = project_snapshot(project)
        action = (
            "project.status_changed"
            if before["status"] != after["status"]
            else "project.updated"
        )
        self.events.audit(
            actor=current_user,
            action=action,
            object_type="project",
            object_id=project.id,
            before=before,
            after=after,
        )
        if (
            before["status"] != ProjectStatus.ACTIVE.value
            and after["status"] == ProjectStatus.ACTIVE.value
        ):
            self.events.publish(
                event_type="ProjectPublished",
                aggregate_type="project",
                aggregate_id=project.id,
                payload={"project_id": str(project.id), "version": project.version},
            )
        project, count = self.get_existing_with_count(project.id)
        return self.to_details(project, count)

    def archive(
        self,
        project_id: UUID,
        current_user: User | None = None,
        expected_version: int | None = None,
    ) -> None:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            self.ensure_can_manage_project(project_id, current_user)
            project = self.get_existing_project(project_id)
            before = project_snapshot(project)
            if self.repo.claim_version(project, expected_version) != 1:
                raise ConflictDetected(
                    "Проект был изменён другим пользователем; обновите данные"
                )
            if project.status == ProjectStatus.ARCHIVED or project.archived_at is not None:
                self.repo.soft_delete(project)
                action = "project.deleted"
            else:
                ensure_project_transition(project.status, ProjectStatus.ARCHIVED)
                self.repo.archive(project)
                action = "project.archived"
                self.events.publish(
                    event_type="ProjectArchived",
                    aggregate_type="project",
                    aggregate_id=project.id,
                    payload={"project_id": str(project.id), "version": project.version},
                )
            self.db.flush()
            self.events.audit(
                actor=current_user,
                action=action,
                object_type="project",
                object_id=project.id,
                before=before,
                after=project_snapshot(project),
            )
            uow.commit()

    def restore(
        self,
        project_id: UUID,
        current_user: User | None = None,
        expected_version: int | None = None,
    ) -> ProjectDetails:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            self.ensure_can_manage_project(project_id, current_user)
            project = self.get_existing_project(project_id)
            if project.status != ProjectStatus.ARCHIVED and project.archived_at is None:
                raise InvalidRequest("Проект не находится в архиве")
            before = project_snapshot(project)
            if self.repo.claim_version(project, expected_version) != 1:
                raise ConflictDetected(
                    "Проект был изменён другим пользователем; обновите данные"
                )
            ensure_project_transition(project.status, ProjectStatus.ACTIVE)
            self.repo.restore_from_archive(project)
            self.db.flush()
            self.events.audit(
                actor=current_user,
                action="project.restored",
                object_type="project",
                object_id=project.id,
                before=before,
                after=project_snapshot(project),
            )
            self.events.publish(
                event_type="ProjectPublished",
                aggregate_type="project",
                aggregate_id=project.id,
                payload={"project_id": str(project.id), "version": project.version},
            )
            project, count = self.get_existing_with_count(project.id)
            result = self.to_details(project, count)
            uow.commit()
            return result
