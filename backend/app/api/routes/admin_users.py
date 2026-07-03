from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.modules.users.schemas import UserRead
from app.modules.users.service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserRead])
def list_admin_users(_: AdminUser, db: DbSession) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in UserService(db).list_all()]
