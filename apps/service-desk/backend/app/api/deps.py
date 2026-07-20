import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header
from platform_sdk.error_types import AuthenticationRequired, PermissionDenied
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.enums import ServiceDeskAccessType
from app.core.security import decode_access_token
from app.modules.access.models import ServiceDeskUser
from app.modules.access.repository import ServiceDeskAccessRepository
from app.modules.access.service import ServiceDeskAccessService

logger = logging.getLogger("service_desk.access")


def get_db() -> Generator[Session]:
    yield from get_session()


DbSession = Annotated[Session, Depends(get_db)]


def get_service_desk_access_status(
    db: Session,
    authorization: str | None,
) -> bool:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationRequired("Требуется авторизация")
    token = authorization.split(" ", maxsplit=1)[1]
    principal = decode_access_token(token)
    if principal.has_permission("platform.admin"):
        return True
    if not principal.has_permission("service_desk.access"):
        return False
    user = ServiceDeskAccessRepository(db).get_by_identity_user_id(principal.user_id)
    return bool(user and user.is_active)


def get_current_service_desk_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> ServiceDeskUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationRequired("Требуется авторизация")
    principal = decode_access_token(authorization.split(" ", maxsplit=1)[1])
    repository = ServiceDeskAccessRepository(db)
    user = repository.get_by_identity_user_id(principal.user_id)
    if principal.has_permission("platform.admin"):
        if user is None:
            user = ServiceDeskUser(
                identity_user_id=principal.user_id,
                email=principal.email
                or f"platform-admin-{principal.user_id}@local.invalid",
                display_name=principal.display_name or "Администратор платформы",
                access_type=ServiceDeskAccessType.SERVICE_DESK_MANAGER,
                is_active=True,
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                user = repository.get_by_identity_user_id(principal.user_id)
                if user is None:
                    raise
        user._is_platform_admin = True
        user._platform_permissions = principal.permissions
        user._platform_principal = principal
        return user
    if "legacy" not in principal.audiences and not principal.has_permission(
        "service_desk.access"
    ):
        raise PermissionDenied("Нет доступа к Service Desk")
    if not user:
        logger.info("service_desk_profile_not_found")
        raise PermissionDenied("Нет доступа к Service Desk")
    if not user.is_active:
        logger.info("service_desk_profile_inactive")
        raise PermissionDenied("Нет доступа к Service Desk")
    user._platform_permissions = principal.permissions
    user._platform_principal = principal
    return user


CurrentServiceDeskUser = Annotated[ServiceDeskUser, Depends(get_current_service_desk_user)]


def require_service_desk_capability(required_capability: str):
    def dependency(current_user: CurrentServiceDeskUser) -> ServiceDeskUser:
        if required_capability not in ServiceDeskAccessService.capabilities_for(current_user):
            raise PermissionDenied(
                "Недостаточно прав для этой операции Service Desk"
            )
        return current_user

    return dependency
