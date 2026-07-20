from __future__ import annotations

import json
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status


@dataclass(frozen=True, slots=True)
class CurrentPrincipal:
    """Verified platform identity delivered to a product module.

    This type intentionally contains no module business roles.  Product
    services combine generic permissions with their own object policy checks.
    """

    user_id: str
    external_subject: str | None
    email: str | None
    display_name: str | None
    permissions: frozenset[str]
    audiences: frozenset[str]
    token_id: str | None = None
    session_version: int | None = None
    correlation_id: str | None = None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "platform.admin" in self.permissions


def principal_from_claims(claims: dict[str, object]) -> CurrentPrincipal:
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("A platform token must contain a subject")
    raw_permissions = claims.get("permissions")
    permissions = (
        frozenset(item for item in raw_permissions if isinstance(item, str))
        if isinstance(raw_permissions, (list, tuple, set, frozenset))
        else frozenset()
    )
    raw_audience = claims.get("aud")
    audiences = (
        frozenset({raw_audience})
        if isinstance(raw_audience, str)
        else (
            frozenset(item for item in raw_audience if isinstance(item, str))
            if isinstance(raw_audience, (list, tuple, set, frozenset))
            else frozenset()
        )
    )
    external_subject = claims.get("external_sub")
    email = claims.get("email")
    display_name = claims.get("display_name")
    token_id = claims.get("jti")
    session_version = claims.get("sv")
    correlation_id = claims.get("cid")
    return CurrentPrincipal(
        user_id=subject,
        external_subject=external_subject if isinstance(external_subject, str) else None,
        email=email if isinstance(email, str) else None,
        display_name=display_name if isinstance(display_name, str) else None,
        permissions=permissions,
        audiences=audiences,
        token_id=token_id if isinstance(token_id, str) else None,
        session_version=session_version if isinstance(session_version, int) else None,
        correlation_id=correlation_id if isinstance(correlation_id, str) else None,
    )


def decode_internal_token(
    token: str,
    *,
    public_key: str,
    audience: str,
    issuer: str = "prom-access",
    algorithms: tuple[str, ...] = ("RS256", "ES256"),
) -> CurrentPrincipal:
    claims = jwt.decode(
        token,
        public_key,
        algorithms=list(algorithms),
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "sub", "jti"]},
    )
    return principal_from_claims(claims)


class CachedJwksVerifier:
    """Verify short-lived platform tokens without an RBAC RPC per request.

    A previously fetched key set remains usable during a bounded Access Service
    outage. Unknown keys fail closed and trigger a refresh attempt.
    """

    def __init__(
        self,
        *,
        jwks_url: str,
        audience: str,
        issuer: str = "prom-access",
        cache_ttl_seconds: int = 300,
        stale_if_error_seconds: int = 3600,
        timeout_seconds: float = 2.0,
        clock_skew_seconds: int = 30,
    ) -> None:
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.cache_ttl_seconds = cache_ttl_seconds
        self.stale_if_error_seconds = stale_if_error_seconds
        self.timeout_seconds = timeout_seconds
        self.clock_skew_seconds = clock_skew_seconds
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at = 0.0
        self._lock = threading.Lock()

    def verify(self, token: str) -> CurrentPrincipal:
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        if not isinstance(key_id, str) or not key_id:
            raise jwt.InvalidTokenError("The platform token has no key id")
        key = self._key(key_id)
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256", "ES256"],
            audience=self.audience,
            issuer=self.issuer,
            leeway=self.clock_skew_seconds,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
        return principal_from_claims(claims)

    def _key(self, key_id: str) -> jwt.PyJWK:
        now = time.monotonic()
        key = self._keys.get(key_id)
        if key is not None and now - self._fetched_at <= self.cache_ttl_seconds:
            return key
        try:
            self._refresh()
        except Exception:
            key = self._keys.get(key_id)
            if key is not None and now - self._fetched_at <= self.stale_if_error_seconds:
                return key
            raise
        key = self._keys.get(key_id)
        if key is None:
            raise jwt.InvalidTokenError("The platform token uses an unknown key")
        return key

    def _refresh(self) -> None:
        with self._lock:
            now = time.monotonic()
            if self._keys and now - self._fetched_at <= self.cache_ttl_seconds:
                return
            request = urllib.request.Request(
                self.jwks_url,
                headers={"Accept": "application/json", "User-Agent": "prom-platform-sdk"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                document = json.load(response)
            raw_keys = document.get("keys") if isinstance(document, dict) else None
            if not isinstance(raw_keys, list) or not raw_keys:
                raise ValueError("JWKS document contains no keys")
            keys: dict[str, jwt.PyJWK] = {}
            for raw_key in raw_keys:
                if not isinstance(raw_key, dict) or not isinstance(raw_key.get("kid"), str):
                    continue
                keys[raw_key["kid"]] = jwt.PyJWK.from_dict(raw_key)
            if not keys:
                raise ValueError("JWKS document contains no usable keys")
            self._keys = keys
            self._fetched_at = time.monotonic()


PrincipalResolver = Callable[[Request], CurrentPrincipal]


def require_permission(permission: str):
    def dependency(request: Request) -> CurrentPrincipal:
        resolver = getattr(request.app.state, "principal_resolver", None)
        if resolver is None:
            raise RuntimeError("The application has no platform principal resolver")
        principal = resolver(request)
        if not principal.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return principal

    return dependency


CurrentPrincipalDependency = Annotated[CurrentPrincipal, Depends(require_permission("platform.authenticated"))]
