from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.enums import UserRole
from app.core.exceptions import DomainError
from app.core.security import decode_access_token
from app.modules.users.models import User
from app.modules.users.service import UserService

DbSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )

    token = authorization.split(" ", maxsplit=1)[1]
    try:
        user_id = UUID(decode_access_token(token))
        return UserService(db).get_by_id(user_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен") from exc


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin_or_manager(current_user: CurrentUser) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.PROJECT_MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return current_user


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return current_user


AdminUser = Annotated[User, Depends(require_admin_or_manager)]
StrictAdminUser = Annotated[User, Depends(require_admin)]
