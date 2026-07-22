from __future__ import annotations

from uuid import UUID

from platform_sdk.error_types import ConflictDetected, EntityNotFound, InvalidRequest
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork

from app.core.enums import UserRole
from app.modules.platform.events import project_snapshot
from app.modules.platform.idempotency import IdempotencyStore, request_fingerprint
from app.modules.projects.schemas import ProjectDetails
from app.modules.projects.service_base import ProjectServiceBase
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class ProjectMembershipService(ProjectServiceBase):
    def add_working_group_member(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        current_user: User,
        idempotency_key: str | None = None,
    ) -> ProjectDetails:
        return self._change_member(
            project_id=project_id,
            user_id=user_id,
            current_user=current_user,
            operation="add",
            idempotency_key=idempotency_key,
        )

    def remove_working_group_member(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        current_user: User,
        idempotency_key: str | None = None,
    ) -> ProjectDetails:
        return self._change_member(
            project_id=project_id,
            user_id=user_id,
            current_user=current_user,
            operation="remove",
            idempotency_key=idempotency_key,
        )

    def _change_member(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        current_user: User,
        operation: str,
        idempotency_key: str | None,
    ) -> ProjectDetails:
        scope = f"{operation.title()}ProjectMember:{project_id}:{current_user.id}"
        request_hash = request_fingerprint(
            {"project_id": str(project_id), "user_id": str(user_id)}
        )
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

            self.ensure_can_manage_project(project_id, current_user)
            project, _ = self.get_existing_with_count(project_id)
            user = UserRepository(self.db).get_by_id(user_id)
            if user is None or user.role == UserRole.PLATFORM_ADMIN:
                raise EntityNotFound("Сотрудник не найден")
            before = project_snapshot(project)
            if self.repo.claim_version(project) != 1:
                raise ConflictDetected(
                    "Проект был изменён другим пользователем; обновите данные"
                )
            if operation == "add":
                self.repo.add_working_group_member(project, user.id)
            else:
                if not self.repo.remove_working_group_member(project, user.id):
                    raise InvalidRequest("Сотрудник не состоит в рабочей группе")
            self.db.flush()
            suffix = "added" if operation == "add" else "removed"
            self.events.audit(
                actor=current_user,
                action=f"project.member_{suffix}",
                object_type="project",
                object_id=project.id,
                before=before,
                after={**project_snapshot(project), "member_user_id": str(user.id)},
            )
            self.events.publish(
                event_type=f"ProjectMember{suffix.title()}",
                aggregate_type="project",
                aggregate_id=project.id,
                payload={"project_id": str(project.id), "user_id": str(user.id)},
            )
            project, count = self.get_existing_with_count(project.id)
            result = self.to_details(project, count)
            store.save(
                scope=scope,
                key=idempotency_key,
                request_hash=request_hash,
                response_status=200,
                response_body=result.model_dump(mode="json"),
            )
            uow.commit()
            return result
