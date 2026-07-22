from datetime import UTC, datetime
from uuid import UUID

from platform_sdk.error_types import ConflictDetected, EntityNotFound, InvalidRequest, PermissionDenied
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectResponseStatus, ProjectStatus
from app.core.permissions import (
    PROJECTS_MANAGE_RESPONSES,
    can_manage_all_projects,
    can_manage_own_projects,
    has_permission,
    is_platform_admin,
)
from app.core.schemas.common import PaginatedResponse
from app.core.security import ensure_utmn_email
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.platform.events import ProjectEventRecorder
from app.modules.platform.idempotency import IdempotencyStore, request_fingerprint
from app.modules.projects.service_base import ProjectServiceBase
from app.modules.responses.models import ProjectResponse
from app.modules.responses.repository import ProjectResponseRepository
from app.modules.responses.schemas import (
    AdminProjectResponseRead,
    ProjectResponseCreate,
    ProjectResponseRead,
    UserProjectResponseRead,
)
from app.modules.responses.workflows import ensure_response_transition
from app.modules.users.models import User


class ProjectResponseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectResponseRepository(db)
        self.events = ProjectEventRecorder(db)

    def create_for_project(
        self,
        project_id: UUID,
        payload: ProjectResponseCreate,
        *,
        current_user: User,
        idempotency_key: str | None = None,
    ) -> ProjectResponseRead:
        scope = f"SubmitProjectResponse:{project_id}:{current_user.id}"
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
                return ProjectResponseRead.model_validate(replay[1])
            result = self._create_for_project(project_id, payload, current_user=current_user)
            store.save(
                scope=scope,
                key=idempotency_key,
                request_hash=request_hash,
                response_status=201,
                response_body=result.model_dump(mode="json"),
            )
            uow.commit()
            return result

    def _create_for_project(
        self,
        project_id: UUID,
        payload: ProjectResponseCreate,
        *,
        current_user: User,
    ) -> ProjectResponseRead:
        project = ProjectServiceBase(self.db).get_existing_project(project_id)
        if project.status not in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED} or project.archived_at is not None:
            raise InvalidRequest("Отклики доступны только для активных и приостановленных проектов")

        email = ensure_utmn_email(payload.email)
        if is_platform_admin(current_user):
            raise PermissionDenied("Администратор не может отправлять отклики на проекты")
        if email != current_user.email:
            raise PermissionDenied("Отклик можно отправить только от своего email")
        if self.repo.exists_for_project_email(project_id, email):
            raise ConflictDetected("Вы уже откликнулись на этот проект")
        data = payload.model_dump()
        data["competencies"] = current_user.competencies
        response = self.repo.create(
            {
                **data,
                "email": email,
                "project_id": project_id,
                "user_id": current_user.id,
                "status": ProjectResponseStatus.NEW,
            }
        )
        self.events.audit(
            actor=current_user,
            action="project.response_submitted",
            object_type="project_response",
            object_id=response.id,
            after=self._audit_snapshot(response),
        )
        self.events.publish(
            event_type="ProjectResponseSubmitted",
            aggregate_type="project_response",
            aggregate_id=response.id,
            payload={
                "response_id": str(response.id),
                "project_id": str(project_id),
                "user_id": str(current_user.id),
            },
        )
        self.db.flush()
        self.db.refresh(response)
        return ProjectResponseRead.model_validate(response)

    def list_admin(
        self,
        *,
        project_id: UUID | None,
        status: ProjectResponseStatus | None,
        search: str | None,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        items, total, safe_limit, safe_offset = self.repo.list_responses(
            project_id=project_id,
            status=status,
            search=search,
            manager_user_id=self._manager_scope_user_id(current_user),
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_admin_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def list_current_user(
        self,
        *,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[UserProjectResponseRead]:
        items, total, safe_limit, safe_offset = self.repo.list_user_responses(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_user_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def list_for_project(
        self,
        *,
        project_id: UUID,
        status: ProjectResponseStatus | None,
        current_user: User,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[AdminProjectResponseRead]:
        ProjectServiceBase(self.db).get_existing_project(project_id)
        self._ensure_can_manage_project(project_id, current_user)
        items, total, safe_limit, safe_offset = self.repo.list_project_responses(
            project_id=project_id,
            status=status,
            manager_user_id=self._manager_scope_user_id(current_user),
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_admin_read(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def update_status(
        self,
        response_id: UUID,
        status: ProjectResponseStatus,
        current_user: User,
    ) -> AdminProjectResponseRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._update_status(response_id, status, current_user)
            uow.commit()
            return result

    def _update_status(
        self,
        response_id: UUID,
        status: ProjectResponseStatus,
        current_user: User,
    ) -> AdminProjectResponseRead:
        response = self.repo.get_by_id(response_id)
        if response is None or response.deleted_at is not None:
            raise EntityNotFound("Отклик не найден")
        self._ensure_can_manage_project(response.project_id, current_user)
        before = self._audit_snapshot(response)
        ensure_response_transition(response.status, status)
        response.status = status
        response.processed_by = current_user.id
        response.processed_at = datetime.now(UTC)
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.response_status_changed",
            object_type="project_response",
            object_id=response.id,
            before=before,
            after=self._audit_snapshot(response),
        )
        if status == ProjectResponseStatus.ACCEPTED:
            self.events.publish(
                event_type="ProjectResponseAccepted",
                aggregate_type="project_response",
                aggregate_id=response.id,
                payload={
                    "response_id": str(response.id),
                    "project_id": str(response.project_id),
                    "user_id": str(response.user_id) if response.user_id else None,
                },
            )
        self.db.refresh(response)
        return self._to_admin_read(response)

    def withdraw_current_user(self, response_id: UUID, current_user: User) -> UserProjectResponseRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._withdraw_current_user(response_id, current_user)
            uow.commit()
            return result

    def _withdraw_current_user(self, response_id: UUID, current_user: User) -> UserProjectResponseRead:
        response = self.repo.get_user_response(response_id, current_user.id)
        if response is None:
            raise EntityNotFound("Отклик не найден")
        if response.status in {ProjectResponseStatus.ACCEPTED, ProjectResponseStatus.REJECTED}:
            raise InvalidRequest("Нельзя отозвать отклик после финального решения")
        before = self._audit_snapshot(response)
        ensure_response_transition(response.status, ProjectResponseStatus.CANCELLED)
        response.status = ProjectResponseStatus.CANCELLED
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.response_withdrawn",
            object_type="project_response",
            object_id=response.id,
            before=before,
            after=self._audit_snapshot(response),
        )
        self.db.refresh(response)
        return self._to_user_read(response)

    def delete_admin(self, response_id: UUID, current_user: User) -> None:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            self._delete_admin(response_id, current_user)
            uow.commit()

    def _delete_admin(self, response_id: UUID, current_user: User) -> None:
        response = self.repo.get_by_id(response_id)
        if response is None or response.deleted_at is not None:
            raise EntityNotFound("Отклик не найден")
        self._ensure_can_manage_project(response.project_id, current_user)
        before = self._audit_snapshot(response)
        self.repo.soft_delete(response)
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.response_deleted",
            object_type="project_response",
            object_id=response.id,
            before=before,
            after=self._audit_snapshot(response),
        )

    @staticmethod
    def _manager_scope_user_id(current_user: User) -> UUID | None:
        if can_manage_all_projects(current_user):
            return None
        return current_user.id

    def _ensure_can_manage_project(self, project_id: UUID, current_user: User) -> None:
        if can_manage_all_projects(current_user):
            return
        if (
            not can_manage_own_projects(current_user)
            or not has_permission(current_user, PROJECTS_MANAGE_RESPONSES)
            or not self.repo.user_can_manage_project(project_id, current_user.id)
        ):
            raise PermissionDenied("Недостаточно прав для работы с откликами этого проекта")

    def _to_admin_read(self, response: ProjectResponse) -> AdminProjectResponseRead:
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.RESPONSE, response.id)
        return AdminProjectResponseRead(
            id=response.id,
            project_id=response.project_id,
            project_title=response.project.title,
            full_name=response.full_name,
            email=response.email,
            comment=response.comment,
            competencies=response.competencies,
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
            status=response.status,
            created_at=response.created_at,
            processed_by=response.processed_by,
            processed_at=response.processed_at,
        )

    def _to_user_read(self, response: ProjectResponse) -> UserProjectResponseRead:
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.RESPONSE, response.id)
        return UserProjectResponseRead(
            id=response.id,
            project_id=response.project_id,
            project_title=response.project.title,
            full_name=response.full_name,
            email=response.email,
            comment=response.comment,
            competencies=response.competencies,
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
            status=response.status,
            created_at=response.created_at,
        )

    @staticmethod
    def _audit_snapshot(response: ProjectResponse) -> dict[str, str | None]:
        return {
            "project_id": str(response.project_id),
            "user_id": str(response.user_id) if response.user_id else None,
            "status": response.status.value,
            "deleted_at": response.deleted_at.isoformat() if response.deleted_at else None,
        }
