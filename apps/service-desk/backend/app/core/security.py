from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import jwt
from platform_sdk.auth import CachedJwksVerifier, CurrentPrincipal
from platform_sdk.error_types import AuthenticationRequired

from app.core.config import settings

PLATFORM_ROLES = {"employee", "project_manager", "platform_admin"}
LEGACY_ROLE_PERMISSIONS = {
    "employee": frozenset({"service_desk.access"}),
    "project_manager": frozenset({"service_desk.access"}),
    "platform_admin": frozenset({"platform.admin"}),
}


def decode_access_token(token: str) -> CurrentPrincipal:
    if settings.access_jwks_url:
        try:
            return _platform_verifier().verify(token)
        except Exception as exc:
            if not settings.allow_legacy_tokens:
                raise AuthenticationRequired("Недействительный токен платформы") from exc
    if not settings.allow_legacy_tokens:
        raise AuthenticationRequired("Платформенная авторизация не настроена")
    return _decode_legacy_token(token)


@lru_cache(maxsize=1)
def _platform_verifier() -> CachedJwksVerifier:
    if not settings.access_jwks_url:
        raise AuthenticationRequired("Платформенная авторизация не настроена")
    return CachedJwksVerifier(
        jwks_url=settings.access_jwks_url,
        audience=settings.access_token_audience,
        issuer=settings.access_token_issuer,
        cache_ttl_seconds=settings.access_jwks_cache_ttl_seconds,
        stale_if_error_seconds=settings.access_jwks_stale_if_error_seconds,
        clock_skew_seconds=settings.access_clock_skew_seconds,
    )


def _decode_legacy_token(token: str) -> CurrentPrincipal:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationRequired("Недействительный токен") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationRequired("Недействительный токен")
    try:
        UUID(subject)
    except ValueError as exc:
        raise AuthenticationRequired("Недействительный токен") from exc
    role = payload.get("platform_role", "employee")
    if role not in PLATFORM_ROLES:
        raise AuthenticationRequired("Недействительная роль платформы")
    permissions = payload.get("permissions")
    if not isinstance(permissions, list):
        permissions = list(LEGACY_ROLE_PERMISSIONS[role])
    return CurrentPrincipal(
        user_id=subject,
        external_subject=None,
        email=payload.get("email") if isinstance(payload.get("email"), str) else None,
        display_name=(
            payload.get("display_name")
            if isinstance(payload.get("display_name"), str)
            else None
        ),
        permissions=frozenset(item for item in permissions if isinstance(item, str)),
        audiences=frozenset({"legacy"}),
        token_id=payload.get("jti") if isinstance(payload.get("jti"), str) else None,
    )
