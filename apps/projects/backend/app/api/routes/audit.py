from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.permissions import PROJECTS_AUDIT_VIEW, has_permission
from platform_sdk.error_types import PermissionDenied
from app.modules.platform.repository import ProjectAuditRepository
from app.modules.platform.schemas import ProjectAuditEventRead

router = APIRouter(prefix="/admin/audit", tags=["projects-audit"])


@router.get("", response_model=list[ProjectAuditEventRead])
def list_audit_events(
    current_user: CurrentUser,
    db: DbSession,
    action: str | None = None,
    object_type: str | None = None,
    object_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ProjectAuditEventRead]:
    if not has_permission(current_user, PROJECTS_AUDIT_VIEW):
        raise PermissionDenied("Недостаточно прав для просмотра аудита Projects")
    return [
        ProjectAuditEventRead.model_validate(event)
        for event in ProjectAuditRepository(db).list_events(
            action=action,
            object_type=object_type,
            object_id=object_id,
            limit=limit,
            offset=offset,
        )
    ]
