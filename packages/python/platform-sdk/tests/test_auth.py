from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from platform_sdk.auth import CachedJwksVerifier, principal_from_claims


def test_principal_from_claims_keeps_session_and_correlation_context() -> None:
    principal = principal_from_claims(
        {
            "sub": "user-1",
            "permissions": ["projects.access"],
            "aud": ["projects"],
            "jti": "token-1",
            "sv": 3,
            "cid": "request-1",
        }
    )

    assert principal.user_id == "user-1"
    assert principal.session_version == 3
    assert principal.correlation_id == "request-1"
    assert principal.has_permission("projects.access")


def test_cached_jwks_verifier_uses_cached_key_during_access_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "iss": "prom-access",
            "sub": "user-1",
            "aud": ["projects"],
            "permissions": ["projects.access"],
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "jti": "token-1",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "key-1"},
    )
    verifier = CachedJwksVerifier(
        jwks_url="http://access.invalid/.well-known/jwks.json",
        audience="projects",
        cache_ttl_seconds=0,
        stale_if_error_seconds=3600,
    )
    verifier._keys = {"key-1": private_key.public_key()}
    verifier._fetched_at = __import__("time").monotonic()

    def fail_refresh() -> None:
        raise OSError("Access Service is unavailable")

    monkeypatch.setattr(verifier, "_refresh", fail_refresh)

    principal = verifier.verify(token)

    assert principal.user_id == "user-1"
    assert principal.permissions == frozenset({"projects.access"})
