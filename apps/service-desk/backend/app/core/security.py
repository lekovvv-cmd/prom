from __future__ import annotations

from functools import lru_cache

from platform_sdk.auth import CachedJwksVerifier, CurrentPrincipal
from platform_sdk.error_types import AuthenticationRequired

from app.core.config import settings


def decode_access_token(token: str) -> CurrentPrincipal:
    try:
        return _platform_verifier().verify(token)
    except Exception as exc:
        raise AuthenticationRequired("Invalid platform token") from exc


@lru_cache(maxsize=1)
def _platform_verifier() -> CachedJwksVerifier:
    if not settings.access_jwks_url:
        raise AuthenticationRequired("Platform authentication is not configured")
    return CachedJwksVerifier(
        jwks_url=settings.access_jwks_url,
        audience=settings.access_token_audience,
        issuer=settings.access_token_issuer,
        cache_ttl_seconds=300,
        stale_if_error_seconds=3600,
        clock_skew_seconds=30,
    )
