from collections.abc import Generator
import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import InvalidAccessTokenError, decode_access_token
from app.modules.access.models import ServiceDeskUser
from app.modules.access.repository import ServiceDeskAccessRepository
from app.modules.access.service import ServiceDeskAccessService


logger = logging.getLogger("service_desk.access")


def get_db() -> Generator[Session]:
    yield from get_session()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_service_desk_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> ServiceDeskUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    token = authorization.split(" ", maxsplit=1)[1]
    try:
        identity_user_id = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    user = ServiceDeskAccessRepository(db).get_by_identity_user_id(identity_user_id)
    if not user:
        logger.info("service_desk_profile_not_found")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
    if not user.is_active:
        logger.info("service_desk_profile_inactive")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
    if "service_desk.access" not in ServiceDeskAccessService.capabilities_for(user):
        logger.info("service_desk_access_capability_missing")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
    return user


CurrentServiceDeskUser = Annotated[ServiceDeskUser, Depends(get_current_service_desk_user)]


def require_service_desk_capability(required_capability: str):
    def dependency(current_user: CurrentServiceDeskUser) -> ServiceDeskUser:
        if required_capability not in ServiceDeskAccessService.capabilities_for(current_user):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для этой операции Service Desk")
        return current_user

    return dependency
