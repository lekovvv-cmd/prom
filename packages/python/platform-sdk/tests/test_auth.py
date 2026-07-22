from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from platform_sdk.auth import CachedJwksVerifier, principal_from_claims


def platform_token(
    private_key: rsa.RSAPrivateKey,
    *,
    kid: str | None = "key-1",
    issuer: str = "prom-access",
    audience: str = "projects",
    expires_at: datetime | None = None,
) -> str:
    now = datetime.now(UTC)
    headers = {"kid": kid} if kid is not None else None
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "user-1",
            "aud": [audience],
            "permissions": ["projects.access"],
            "iat": now,
            "exp": expires_at or now + timedelta(minutes=5),
            "jti": "token-1",
        },
        private_key,
        algorithm="RS256",
        headers=headers,
    )


def verifier_with_key(
    private_key: rsa.RSAPrivateKey,
    *,
    audience: str = "projects",
    issuer: str = "prom-access",
) -> CachedJwksVerifier:
    verifier = CachedJwksVerifier(
        jwks_url="http://access.invalid/.well-known/jwks.json",
        audience=audience,
        issuer=issuer,
        cache_ttl_seconds=300,
    )
    verifier._keys = {"key-1": private_key.public_key()}
    verifier._fetched_at = __import__("time").monotonic()
    return verifier


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


def test_cached_jwks_verifier_accepts_a_valid_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    principal = verifier_with_key(private_key).verify(platform_token(private_key))

    assert principal.user_id == "user-1"
    assert principal.audiences == frozenset({"projects"})


@pytest.mark.parametrize(
    "token_factory",
    [
        lambda key: platform_token(
            key,
            expires_at=datetime.now(UTC) - timedelta(minutes=2),
        ),
        lambda key: platform_token(key, issuer="wrong-issuer"),
        lambda key: platform_token(key, audience="service-desk"),
        lambda key: platform_token(key, kid=None),
        lambda key: platform_token(key, kid="unknown-key"),
        lambda key: platform_token(
            rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ),
    ],
    ids=[
        "expired",
        "wrong-issuer",
        "wrong-audience",
        "missing-kid",
        "unknown-kid",
        "tampered-signature",
    ],
)
def test_cached_jwks_verifier_rejects_invalid_tokens(token_factory) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(jwt.PyJWTError):
        verifier_with_key(private_key).verify(token_factory(private_key))


def test_cached_jwks_verifier_rejects_an_overage_cache_during_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = verifier_with_key(private_key)
    verifier.cache_ttl_seconds = 0
    verifier.stale_if_error_seconds = 1
    verifier._fetched_at = __import__("time").monotonic() - 2

    def fail_refresh() -> None:
        raise OSError("Access Service is unavailable")

    monkeypatch.setattr(verifier, "_refresh", fail_refresh)

    with pytest.raises(OSError, match="unavailable"):
        verifier.verify(platform_token(private_key))
