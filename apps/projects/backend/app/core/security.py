from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from platform_sdk.auth import CachedJwksVerifier, CurrentPrincipal
from platform_sdk.error_types import AuthenticationRequired, ValidationFailed

from app.core.config import settings
from app.core.enums import UserRole

UTMN_EMAIL_PATTERN = re.compile(r"^[^\s@]+@utmn\.ru$")

LEGACY_PERMISSIONS = {
    UserRole.EMPLOYEE: {
        "projects.access",
        "projects.view",
        "projects.respond",
    },
    UserRole.PROJECT_MANAGER: {
        "projects.access",
        "projects.view",
        "projects.respond",
        "projects.create",
        "projects.manage_own",
        "projects.manage_members",
        "projects.manage_responses",
        "projects.manage_tasks",
        "projects.manage_reports",
    },
    UserRole.PLATFORM_ADMIN: {"platform.admin", "projects.manage_all"},
}


def create_access_token(
    subject: str,
    platform_role: UserRole,
    expires_delta: timedelta | None = None,
) -> str:
    """Test-only compatibility token for the announced migration window."""

    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "platform_role": platform_role.value,
        "permissions": sorted(LEGACY_PERMISSIONS[platform_role]),
        "iat": datetime.now(UTC),
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> CurrentPrincipal:
    if settings.access_jwks_url:
        try:
            return _platform_verifier().verify(token)
        except Exception as exc:
            if not settings.allow_legacy_tokens:
                raise AuthenticationRequired(
                    "Недействительный токен платформы"
                ) from exc
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
    role_value = payload.get("platform_role", UserRole.EMPLOYEE.value)
    try:
        role = UserRole(role_value)
    except ValueError as exc:
        raise AuthenticationRequired("Недействительная роль платформы") from exc
    permissions = payload.get("permissions")
    if not isinstance(permissions, list):
        permissions = list(LEGACY_PERMISSIONS[role])
    return CurrentPrincipal(
        user_id=subject,
        external_subject=None,
        email=payload.get("email")
        if isinstance(payload.get("email"), str)
        else None,
        display_name=None,
        permissions=frozenset(
            item for item in permissions if isinstance(item, str)
        ),
        audiences=frozenset({settings.access_token_audience}),
        token_id=payload.get("jti")
        if isinstance(payload.get("jti"), str)
        else None,
    )


def is_utmn_email(email: str) -> bool:
    return bool(UTMN_EMAIL_PATTERN.fullmatch(email.strip().lower()))


def ensure_utmn_email(email: str) -> str:
    normalized = email.strip().lower()
    if not is_utmn_email(normalized):
        raise ValidationFailed(
            "Разрешены только email на домене @utmn.ru"
        )
    return normalized
