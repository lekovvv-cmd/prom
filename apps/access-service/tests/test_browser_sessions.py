from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from access_service.api.router import safe_return_url
from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import Base, BrowserSession, PlatformUser
from access_service.infrastructure.identity import generate_private_key_pem
from access_service.infrastructure.sessions import BrowserSessionManager


def make_request(
    credentials,
    *,
    method: str = "GET",
    include_csrf_header: bool = True,
) -> Request:
    cookie = (
        f"prom_session={credentials.session_secret}; "
        f"prom_csrf={credentials.csrf_token}"
    )
    headers = [(b"cookie", cookie.encode())]
    if include_csrf_header:
        headers.append((b"x-csrf-token", credentials.csrf_token.encode()))
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/session",
            "headers": headers,
            "client": ("127.0.0.1", 5000),
            "server": ("test", 80),
            "scheme": "https",
            "query_string": b"",
        }
    )


def create_session(settings: AccessSettings):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine, expire_on_commit=False)
    user = PlatformUser(
        id="user-1",
        email="user@utmn.ru",
        display_name="User",
    )
    db.add(user)
    db.commit()
    manager = BrowserSessionManager(settings)
    credentials = manager.create(db, user)
    db.commit()
    return engine, db, user, manager, credentials


def test_cookie_flags_keep_session_secret_http_only() -> None:
    settings = AccessSettings(database_url="sqlite+pysqlite:///:memory:")
    engine, db, _, manager, credentials = create_session(settings)
    response = Response()
    manager.set_cookies(response, credentials)
    cookies = response.headers.getlist("set-cookie")
    session_cookie = next(cookie for cookie in cookies if cookie.startswith("prom_session="))
    csrf_cookie = next(cookie for cookie in cookies if cookie.startswith("prom_csrf="))
    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie
    assert "Secure" not in session_cookie
    assert "HttpOnly" not in csrf_cookie
    assert credentials.session_secret not in response.body.decode()
    db.close()
    engine.dispose()


def test_production_session_cookie_is_secure() -> None:
    settings = AccessSettings(
        environment="production",
        database_url="postgresql+psycopg://access:secret@db/access",
        frontend_origin="https://prom.example",
        token_issuer="https://prom.example/access",
        jwt_private_key=generate_private_key_pem(),
        jwt_key_id="production-key",
        sso_provider="oidc",
        oidc_enabled=True,
        oidc_issuer_url="https://sso.example",
        oidc_client_id="prom",
        oidc_client_secret="client-secret",
        oidc_redirect_uri="https://prom.example/auth/callback",
    )
    manager = BrowserSessionManager(settings)
    response = Response()
    from access_service.infrastructure.sessions import BrowserSessionCredentials

    manager.set_cookies(response, BrowserSessionCredentials("secret", "csrf"))
    session_cookie = next(
        cookie
        for cookie in response.headers.getlist("set-cookie")
        if cookie.startswith("prom_session=")
    )
    assert "Secure" in session_cookie
    assert "HttpOnly" in session_cookie


def test_csrf_is_required_for_state_changes() -> None:
    settings = AccessSettings(database_url="sqlite+pysqlite:///:memory:")
    engine, db, user, manager, credentials = create_session(settings)
    with pytest.raises(HTTPException) as error:
        manager.authenticate(
            make_request(credentials, method="POST", include_csrf_header=False),
            Response(),
            db,
        )
    assert error.value.status_code == 403
    authenticated = manager.authenticate(
        make_request(credentials, method="POST"),
        Response(),
        db,
    )
    assert authenticated.id == user.id
    db.close()
    engine.dispose()


def test_revoked_disabled_and_expired_sessions_fail_closed() -> None:
    settings = AccessSettings(database_url="sqlite+pysqlite:///:memory:")
    engine, db, user, manager, credentials = create_session(settings)
    user.session_version += 1
    db.commit()
    response = Response()
    with pytest.raises(HTTPException) as error:
        manager.authenticate(make_request(credentials), response, db)
    assert error.value.status_code == 401
    assert any(
        "prom_session=" in cookie and "Max-Age=0" in cookie
        for cookie in response.headers.getlist("set-cookie")
    )

    browser_session = db.scalar(select(BrowserSession))
    assert browser_session is not None
    browser_session.revoked_at = None
    browser_session.session_version = user.session_version
    browser_session.idle_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    with pytest.raises(HTTPException):
        manager.authenticate(make_request(credentials), Response(), db)
    db.close()
    engine.dispose()


def test_session_secret_rotates_without_extending_absolute_expiry() -> None:
    settings = AccessSettings(
        database_url="sqlite+pysqlite:///:memory:",
        session_rotation_seconds=1,
    )
    engine, db, _, manager, credentials = create_session(settings)
    browser_session = db.scalar(select(BrowserSession))
    assert browser_session is not None
    absolute_expiry = browser_session.absolute_expires_at
    browser_session.rotated_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    db.commit()
    response = Response()
    manager.authenticate(make_request(credentials), response, db)
    db.refresh(browser_session)
    assert browser_session.absolute_expires_at == absolute_expiry
    assert any(
        cookie.startswith("prom_session=")
        and credentials.session_secret not in cookie
        for cookie in response.headers.getlist("set-cookie")
    )
    db.close()
    engine.dispose()


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("/projects", "/projects"),
        ("//evil.example", "/"),
        ("https://evil.example", "/"),
        ("javascript:alert(1)", "/"),
    ],
)
def test_return_url_is_local(candidate: str, expected: str) -> None:
    assert safe_return_url(candidate) == expected

