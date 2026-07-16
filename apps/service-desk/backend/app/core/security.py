from dataclasses import dataclass
from functools import lru_cache
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
    if settings.access_jwks_url:
        try:
            return decode_platform_access_token(token)
        except InvalidAccessTokenError:
            # Compatibility tokens are accepted until the old login endpoint is
            # removed in a separately announced deprecation release.
            pass
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


@lru_cache(maxsize=2)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_jwk_set=True, lifespan=300)


def decode_platform_access_token(token: str) -> AccessTokenClaims:
    if not settings.access_jwks_url:
        raise InvalidAccessTokenError("Платформенная авторизация не настроена")
    try:
        signing_key = _jwks_client(settings.access_jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="service-desk",
            issuer=settings.access_token_issuer,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessTokenError("Недействительный токен платформы") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidAccessTokenError("Недействительный токен платформы")
    permissions = payload.get("permissions", [])
    is_platform_admin = isinstance(permissions, list) and "platform.admin" in permissions
    return AccessTokenClaims(
        subject=subject,
        platform_role="platform_admin" if is_platform_admin else None,
    )
