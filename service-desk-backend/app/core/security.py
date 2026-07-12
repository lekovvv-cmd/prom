from dataclasses import dataclass
from uuid import UUID

import jwt

from app.core.config import settings


class InvalidAccessTokenError(ValueError):
    pass


PLATFORM_ROLES = {"employee", "project_manager", "platform_admin"}


@dataclass(frozen=True)
class AccessTokenClaims:
    subject: str
    platform_role: str | None


def decode_access_token(token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidAccessTokenError("Недействительный токен") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidAccessTokenError("Недействительный токен")
    try:
        UUID(subject)
    except ValueError as exc:
        raise InvalidAccessTokenError("Недействительный токен") from exc

    platform_role = payload.get("platform_role")
    if platform_role is not None and platform_role not in PLATFORM_ROLES:
        raise InvalidAccessTokenError("Недействительная роль платформы")
    return AccessTokenClaims(subject=subject, platform_role=platform_role)
