from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.modules.users.schemas import (
    AuthCodeResponse,
    AuthEmailRequest,
    AuthVerifyRequest,
    TokenResponse,
    UserRead,
)
from app.modules.users.service import UserService

router = APIRouter(tags=["auth"])


@router.post("/auth/request-code", response_model=AuthCodeResponse)
def request_code(payload: AuthEmailRequest, db: DbSession) -> dict[str, str]:
    return UserService(db).request_code(payload.email)


@router.post("/auth/verify-code", response_model=TokenResponse)
def verify_code(payload: AuthVerifyRequest, db: DbSession) -> TokenResponse:
    user, token = UserService(db).verify_code(payload.email, payload.code)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
