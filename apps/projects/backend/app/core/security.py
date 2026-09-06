from __future__ import annotations

import re
from functools import lru_cache

from platform_sdk.auth import CachedJwksVerifier, CurrentPrincipal
from platform_sdk.error_types import AuthenticationRequired, ValidationFailed

from app.core.config import settings

UTMN_EMAIL_PATTERN = re.compile(r"^[^\s@]+@utmn\.ru$")

def decode_access_token(token: str) -> CurrentPrincipal:
    try:
        return _platform_verifier().verify(token)
    except Exception as exc:
        raise AuthenticationRequired("Недействительный токен платформы") from exc


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


def is_utmn_email(email: str) -> bool:
    return bool(UTMN_EMAIL_PATTERN.fullmatch(email.strip().lower()))


def ensure_utmn_email(email: str) -> str:
    normalized = email.strip().lower()
    if not is_utmn_email(normalized):
        raise ValidationFailed(
            "Разрешены только email на домене @utmn.ru"
        )
    return normalized
