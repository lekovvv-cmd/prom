from __future__ import annotations

from datetime import UTC, datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import jwt
import pytest
from pydantic import ValidationError

from access_service.bootstrap.config import AccessSettings
from access_service.infrastructure.identity import InternalTokenSigner


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


def test_single_signing_key_is_published_and_verifies_tokens() -> None:
    signer = InternalTokenSigner(
        AccessSettings(database_url="sqlite+pysqlite:///:memory:", jwt_key_id="test-key")
    )
    token = signer.issue(
        user_id="user-1",
        external_subject=None,
        email="employee@utmn.ru",
        display_name="Employee",
        permissions={"projects.access"},
        session_version=1,
    )

    assert [key["kid"] for key in signer.jwks()["keys"]] == ["test-key"]
    assert signer.verify(token, audience="projects")["sub"] == "user-1"



def production_settings(**overrides: object) -> AccessSettings:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    values: dict[str, object] = {
        "environment": "production",
        "database_url": "postgresql+psycopg://access:secret@db/access",
        "token_issuer": "https://prom.example/access",
        "token_audiences": "projects,service-desk",
        "jwt_private_key": private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode(),
        "jwt_key_id": "production-2026-07",
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
        ({"token_issuer": ""}, "ACCESS_TOKEN_ISSUER"),
        ({"token_audiences": ""}, "ACCESS_TOKEN_AUDIENCES"),
    ],
)
def test_production_settings_reject_unsafe_configuration(
    override: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        production_settings(**override)


def test_production_settings_accept_valid_configuration() -> None:
    configured = production_settings()

    assert configured.token_audience_values == ("projects", "service-desk")
