from typing import Annotated
from fastapi import Depends, Header
from platform_sdk.error_types import AuthenticationRequired, PermissionDenied
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.permissions import (
    PROJECTS_MANAGE_ALL,
    PROJECTS_MANAGE_OWN,
    has_any_permission,
    has_permission,
)
from app.core.security import decode_access_token
from app.modules.users.models import User
from app.modules.users.service import UserService

DbSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationRequired("Требуется авторизация")

    token = authorization.split(" ", maxsplit=1)[1]
    return UserService(db).sync_principal(decode_access_token(token))


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin_or_manager(current_user: CurrentUser) -> User:
    if not has_any_permission(current_user, PROJECTS_MANAGE_OWN, PROJECTS_MANAGE_ALL):
        raise PermissionDenied("Недостаточно прав для управления проектами")
    return current_user


def require_admin(current_user: CurrentUser) -> User:
    if not has_permission(current_user, PROJECTS_MANAGE_ALL):
        raise PermissionDenied("Недостаточно прав для администрирования модуля Projects")
    return current_user


AdminUser = Annotated[User, Depends(require_admin_or_manager)]
StrictAdminUser = Annotated[User, Depends(require_admin)]
