from collections.abc import Generator
import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.enums import ServiceDeskAccessType
from app.core.security import InvalidAccessTokenError, decode_access_token
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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    token = authorization.split(" ", maxsplit=1)[1]
    try:
        claims = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    if claims.platform_role == "platform_admin":
        return True
    user = ServiceDeskAccessRepository(db).get_by_identity_user_id(claims.subject)
    return bool(user and user.is_active)


def get_current_service_desk_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> ServiceDeskUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    try:
        claims = decode_access_token(authorization.split(" ", maxsplit=1)[1])
    except InvalidAccessTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    repository = ServiceDeskAccessRepository(db)
    user = repository.get_by_identity_user_id(claims.subject)
    if claims.platform_role == "platform_admin":
        if user is None:
            user = ServiceDeskUser(
                identity_user_id=claims.subject,
                email=f"platform-admin-{claims.subject}@local.invalid",
                display_name="Администратор платформы",
                access_type=ServiceDeskAccessType.SERVICE_DESK_MANAGER,
                is_active=True,
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                user = repository.get_by_identity_user_id(claims.subject)
                if user is None:
                    raise
        user._is_platform_admin = True
        return user
    if not user:
        logger.info("service_desk_profile_not_found")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
    if not user.is_active:
        logger.info("service_desk_profile_inactive")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
    return user


CurrentServiceDeskUser = Annotated[ServiceDeskUser, Depends(get_current_service_desk_user)]


def require_service_desk_capability(required_capability: str):
    def dependency(current_user: CurrentServiceDeskUser) -> ServiceDeskUser:
        if required_capability not in ServiceDeskAccessService.capabilities_for(current_user):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для этой операции Service Desk")
        return current_user

    return dependency
