from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlencode, urlparse

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import Base, OidcLoginTransaction
from access_service.infrastructure.identity import (
    InternalTokenSigner,
    OidcIdentityProvider,
    TrustedHeaderIdentityProvider,
)
from access_service.infrastructure import identity as identity_module


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


@pytest.fixture
def oidc_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    yield factory
    engine.dispose()


def configured_provider(oidc_session_factory) -> OidcIdentityProvider:
    return OidcIdentityProvider(production_settings(), oidc_session_factory)


def start_login(
    provider: OidcIdentityProvider,
    monkeypatch: pytest.MonkeyPatch,
    return_url: str = "/projects",
) -> dict[str, str]:
    monkeypatch.setattr(
        provider,
        "_discovery_document",
        lambda: {"authorization_endpoint": "https://sso.example/authorize"},
    )
    redirect = provider.build_login_redirect(return_url)
    return {key: values[0] for key, values in parse_qs(urlparse(redirect).query).items()}


def transaction_for(provider: OidcIdentityProvider, state: str) -> OidcLoginTransaction:
    with provider.session_factory() as session:
        transaction = session.scalar(
            select(OidcLoginTransaction).where(
                OidcLoginTransaction.state_hash == provider._state_hash(state)
            )
        )
        assert transaction is not None
        return transaction


def install_token_exchange(
    provider: OidcIdentityProvider,
    monkeypatch: pytest.MonkeyPatch,
    *,
    nonce: str,
    observed_payloads: list[dict[str, str]],
) -> None:
    identity_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(UTC)
    id_token = jwt.encode(
        {
            "iss": provider.settings.oidc_issuer_url,
            "sub": "oidc-user",
            "aud": provider.settings.oidc_client_id,
            "email": "oidc.user@utmn.ru",
            "name": "OIDC User",
            "nonce": nonce,
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        identity_key,
        algorithm="RS256",
        headers={"kid": "oidc-key"},
    )
    monkeypatch.setattr(
        provider,
        "_discovery_document",
        lambda: {
            "token_endpoint": "https://sso.example/token",
            "jwks_uri": "https://sso.example/jwks",
        },
    )

    class TokenResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"id_token": id_token}

    class JwkClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str) -> SimpleNamespace:
            return SimpleNamespace(key=identity_key.public_key())

    def token_post(*_args, **kwargs):
        observed_payloads.append(kwargs["data"])
        return TokenResponse()

    monkeypatch.setattr(identity_module.httpx, "post", token_post)
    monkeypatch.setattr(identity_module.jwt, "PyJWKClient", JwkClient)


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


def test_oidc_adapter_is_complete_but_disabled_without_real_settings(
    oidc_session_factory,
) -> None:
    provider = OidcIdentityProvider(
        AccessSettings(database_url="sqlite+pysqlite:///:memory:"),
        oidc_session_factory,
    )

    with pytest.raises(HTTPException) as error:
        provider.build_login_redirect("/")

    assert error.value.status_code == 503


def test_oidc_login_persists_opaque_state_nonce_pkce_and_safe_return_url(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    query = start_login(provider, monkeypatch, "https://evil.example/steal")
    transaction = transaction_for(provider, query["state"])
    expected_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(transaction.pkce_verifier.encode()).digest()
        )
        .rstrip(b"=")
        .decode()
    )

    assert transaction.state_hash == provider._state_hash(query["state"])
    assert transaction.state_hash != query["state"]
    assert transaction.return_url == "/"
    assert transaction.nonce == query["nonce"]
    assert query["code_challenge"] == expected_challenge
    assert query["code_challenge_method"] == "S256"
    assert transaction.pkce_verifier not in query.values()
    assert transaction.pkce_verifier not in query["state"]


def test_oidc_callback_rejects_unknown_or_intercepted_state_before_token_exchange(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    token_calls: list[dict[str, str]] = []
    monkeypatch.setattr(
        identity_module.httpx,
        "post",
        lambda *_args, **kwargs: token_calls.append(kwargs["data"]),
    )
    request = make_request()
    request.scope["query_string"] = b"code=intercepted-code&state=unknown-state"

    with pytest.raises(HTTPException) as error:
        provider.handle_callback(request)

    assert error.value.status_code == 400
    assert token_calls == []


def test_oidc_callback_rejects_nonce_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    query = start_login(provider, monkeypatch)
    transaction = transaction_for(provider, query["state"])
    observed_payloads: list[dict[str, str]] = []
    install_token_exchange(
        provider,
        monkeypatch,
        nonce="different-nonce",
        observed_payloads=observed_payloads,
    )
    request = make_request()
    request.scope["query_string"] = urlencode(
        {"code": "auth-code", "state": query["state"]}
    ).encode()

    with pytest.raises(HTTPException) as error:
        provider.handle_callback(request)

    assert error.value.status_code == 401
    assert error.value.detail == "OIDC nonce mismatch"
    assert observed_payloads[0]["code_verifier"] == transaction.pkce_verifier


def test_oidc_callback_claims_once_before_token_exchange(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    query = start_login(provider, monkeypatch)
    transaction = transaction_for(provider, query["state"])
    observed_payloads: list[dict[str, str]] = []
    install_token_exchange(
        provider,
        monkeypatch,
        nonce=transaction.nonce,
        observed_payloads=observed_payloads,
    )
    request = make_request()
    request.scope["query_string"] = urlencode(
        {"code": "auth-code", "state": query["state"]}
    ).encode()

    principal = provider.handle_callback(request)
    assert principal.subject == "oidc-user"
    assert principal.return_url == "/projects"
    assert observed_payloads == [
        {
            "grant_type": "authorization_code",
            "code": "auth-code",
            "redirect_uri": provider.settings.oidc_redirect_uri,
            "client_id": provider.settings.oidc_client_id,
            "client_secret": provider.settings.oidc_client_secret,
            "code_verifier": transaction.pkce_verifier,
        }
    ]

    with pytest.raises(HTTPException) as error:
        provider.handle_callback(request)
    assert error.value.status_code == 400
    assert len(observed_payloads) == 1


def test_oidc_callback_rejects_expired_transaction(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    query = start_login(provider, monkeypatch)
    with provider.session_factory() as session:
        transaction = transaction_for(provider, query["state"])
        transaction.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.merge(transaction)
        session.commit()
    with pytest.raises(HTTPException) as error:
        provider.handle_callback(
            Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/",
                    "headers": [],
                    "client": ("127.0.0.1", 5000),
                    "server": ("test", 80),
                    "scheme": "https",
                    "query_string": urlencode(
                        {"code": "auth-code", "state": query["state"]}
                    ).encode(),
                }
            )
        )
    assert error.value.status_code == 400


def test_oidc_token_exchange_failure_does_not_restore_claimed_state(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    query = start_login(provider, monkeypatch)
    calls = 0

    def unavailable(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise identity_module.httpx.ConnectError("SSO unavailable")

    monkeypatch.setattr(
        provider,
        "_discovery_document",
        lambda: {"token_endpoint": "https://sso.example/token", "jwks_uri": "https://sso.example/jwks"},
    )
    monkeypatch.setattr(identity_module.httpx, "post", unavailable)
    request = make_request()
    request.scope["query_string"] = urlencode(
        {"code": "auth-code", "state": query["state"]}
    ).encode()

    with pytest.raises(HTTPException) as error:
        provider.handle_callback(request)
    assert error.value.status_code == 502
    with pytest.raises(HTTPException) as replay:
        provider.handle_callback(request)
    assert replay.value.status_code == 400
    assert calls == 1


def test_oidc_login_bounded_cleanup_removes_only_stale_transactions(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    now = datetime.now(UTC)
    with provider.session_factory() as session:
        session.add_all(
            [
                OidcLoginTransaction(
                    state_hash=provider._state_hash("expired"),
                    nonce="expired-nonce",
                    pkce_verifier="expired-verifier",
                    return_url="/",
                    created_at=now - timedelta(minutes=20),
                    expires_at=now - timedelta(minutes=10),
                ),
                OidcLoginTransaction(
                    state_hash=provider._state_hash("consumed"),
                    nonce="consumed-nonce",
                    pkce_verifier="consumed-verifier",
                    return_url="/",
                    created_at=now - timedelta(minutes=20),
                    expires_at=now + timedelta(minutes=5),
                    consumed_at=now - timedelta(minutes=10),
                ),
                OidcLoginTransaction(
                    state_hash=provider._state_hash("active"),
                    nonce="active-nonce",
                    pkce_verifier="active-verifier",
                    return_url="/",
                    created_at=now,
                    expires_at=now + timedelta(minutes=5),
                ),
            ]
        )
        session.commit()

    start_login(provider, monkeypatch)

    with provider.session_factory() as session:
        hashes = set(session.scalars(select(OidcLoginTransaction.state_hash)))
    assert provider._state_hash("expired") not in hashes
    assert provider._state_hash("consumed") not in hashes
    assert provider._state_hash("active") in hashes


def test_oidc_parallel_valid_transactions_keep_their_own_verifiers(
    monkeypatch: pytest.MonkeyPatch,
    oidc_session_factory,
) -> None:
    provider = configured_provider(oidc_session_factory)
    first = start_login(provider, monkeypatch, "/projects")
    second = start_login(provider, monkeypatch, "/service-desk")
    first_transaction = transaction_for(provider, first["state"])
    second_transaction = transaction_for(provider, second["state"])

    claimed_first = provider._claim_transaction(first["state"])
    claimed_second = provider._claim_transaction(second["state"])

    assert claimed_first.pkce_verifier == first_transaction.pkce_verifier
    assert claimed_second.pkce_verifier == second_transaction.pkce_verifier
    assert claimed_first.pkce_verifier != claimed_second.pkce_verifier
    assert claimed_first.return_url == "/projects"
    assert claimed_second.return_url == "/service-desk"


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
        "oidc_client_secret": "oidc-client-secret-at-least-32-bytes",
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
        ({"oidc_client_secret": "too-short"}, "SSO_CLIENT_SECRET"),
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
