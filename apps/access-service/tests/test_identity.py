from __future__ import annotations

from datetime import UTC, datetime

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from access_service.bootstrap.config import AccessSettings
from access_service.infrastructure.identity import (
    InternalTokenSigner,
    OidcIdentityProvider,
    TrustedHeaderIdentityProvider,
)


def make_request(
    *,
    client: tuple[str, int] = ("127.0.0.1", 5000),
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers or [],
            "client": client,
            "server": ("test", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_internal_token_contains_session_version_and_correlation_id() -> None:
    settings = AccessSettings(
        database_url="sqlite+pysqlite:///:memory:",
        jwt_key_id="test-key",
    )
    signer = InternalTokenSigner(settings)

    token = signer.issue(
        user_id="user-1",
        external_subject="external-1",
        email="employee@utmn.ru",
        display_name="Employee",
        permissions={"projects.access"},
        session_version=4,
        correlation_id="request-1",
    )
    claims = jwt.decode(
        token,
        signer.public_key,
        algorithms=["RS256"],
        audience="projects",
        issuer="prom-access",
    )

    assert claims["sv"] == 4
    assert claims["cid"] == "request-1"
    assert datetime.fromtimestamp(claims["exp"], UTC) > datetime.now(UTC)


def test_trusted_headers_require_a_configured_proxy_network() -> None:
    settings = AccessSettings(
        database_url="sqlite+pysqlite:///:memory:",
        trusted_headers_enabled=True,
        trusted_proxy_networks="10.0.0.0/8",
    )
    provider = TrustedHeaderIdentityProvider(settings)
    request = make_request(
        headers=[
            (b"x-forwarded-user", b"subject-1"),
            (b"x-forwarded-email", b"employee@utmn.ru"),
            (b"x-forwarded-name", b"Employee"),
        ]
    )

    with pytest.raises(HTTPException) as error:
        provider.authenticate_request(request)

    assert error.value.status_code == 403


def test_oidc_adapter_is_complete_but_disabled_without_real_settings() -> None:
    provider = OidcIdentityProvider(
        AccessSettings(database_url="sqlite+pysqlite:///:memory:")
    )

    with pytest.raises(HTTPException) as error:
        provider.build_login_redirect("/")

    assert error.value.status_code == 503


def production_settings(**overrides: object) -> AccessSettings:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    values: dict[str, object] = {
        "environment": "production",
        "database_url": "postgresql+psycopg://access:secret@db/access",
        "frontend_origin": "https://prom.example",
        "token_issuer": "https://prom.example/access",
        "token_audiences": "projects,service-desk",
        "jwt_private_key": private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode(),
        "jwt_key_id": "production-2026-07",
        "sso_provider": "oidc",
        "oidc_enabled": True,
        "oidc_issuer_url": "https://sso.example",
        "oidc_client_id": "prom",
        "oidc_client_secret": "oidc-client-secret",
        "oidc_redirect_uri": "https://prom.example/api/access/v1/auth/callback",
    }
    values.update(overrides)
    return AccessSettings(**values)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"database_url": "postgresql+psycopg://access@db/access"}, "non-empty password"),
        ({"debug": True}, "ACCESS_DEBUG"),
        ({"jwt_private_key": ""}, "ACCESS_JWT_PRIVATE_KEY"),
        ({"jwt_key_id": "local-ephemeral"}, "ACCESS_JWT_KEY_ID"),
        ({"frontend_origin": "https://prom.example,*"}, "ACCESS_FRONTEND_ORIGIN"),
        ({"token_issuer": ""}, "ACCESS_TOKEN_ISSUER"),
        ({"token_audiences": ""}, "ACCESS_TOKEN_AUDIENCES"),
        ({"sso_provider": "mock", "oidc_enabled": False}, "SSO_PROVIDER=mock"),
    ],
)
def test_production_settings_reject_unsafe_configuration(
    override: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        production_settings(**override)


def test_production_settings_accept_complete_oidc_configuration() -> None:
    configured = production_settings()

    assert configured.token_audience_values == ("projects", "service-desk")
