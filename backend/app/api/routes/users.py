from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.modules.users.schemas import UserRead
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/directory", response_model=list[UserRead])
def list_user_directory(
    _: AdminUser,
    db: DbSession,
    search: str | None = None,
) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in UserService(db).list_directory(search)]
