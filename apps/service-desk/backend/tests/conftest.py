# ruff: noqa: E402

import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from platform_sdk.auth import decode_internal_token
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.core.enums import ServiceDeskAccessType
from app.main import create_app
from app.modules.access import models as access_models  # noqa: F401
from app.modules.attachments import models as attachment_models  # noqa: F401
from app.modules.access.models import ServiceDeskUser
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.comments import models as comment_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.routing import models as routing_models  # noqa: F401
from app.modules.sla import models as sla_models  # noqa: F401
from app.modules.templates import models as template_models  # noqa: F401
from app.modules.tickets import models as ticket_models  # noqa: F401

TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_PUBLIC_KEY = TEST_PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
).decode()


def sign_platform_token(subject: str, *, permissions: list[str] | None = None, key=None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "iss": settings.access_token_issuer,
            "aud": settings.access_token_audience,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "jti": str(uuid.uuid4()),
            "permissions": permissions or ["service_desk.access"],
        },
        key or TEST_PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": "test-access"},
    )


class LocalVerifier:
    def verify(self, token: str):
        return decode_internal_token(
            token, public_key=TEST_PUBLIC_KEY,
            audience=settings.access_token_audience,
            issuer=settings.access_token_issuer,
        )


@pytest.fixture(autouse=True)
def use_local_platform_verifier(monkeypatch):
    monkeypatch.setattr("app.core.security._platform_verifier", lambda: LocalVerifier())


class ServiceDeskTestClient(TestClient):
    def __init__(self, app, admin_headers_factory) -> None:
        super().__init__(app)
        self._admin_headers_factory = admin_headers_factory
        self._admin_headers: dict[str, str] | None = None

    @property
    def admin_headers(self) -> dict[str, str]:
        if self._admin_headers is None:
            self._admin_headers = self._admin_headers_factory()
        return self._admin_headers

    def request(self, method, url, *args, **kwargs):
        if str(url).startswith("/admin") and kwargs.get("headers") is None:
            kwargs["headers"] = self.admin_headers
        if str(url).startswith("/") and not str(url).startswith(("/health/", "/api/v1/")):
            url = f"/api/v1{url}"
        return super().request(method, url, *args, **kwargs)


@pytest.fixture()
def db_session_factory():
    postgres_url = os.getenv("SERVICE_DESK_TEST_DATABASE_URL")
    engine = create_engine(postgres_url) if postgres_url else create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session_factory):
    def build_admin_headers() -> dict[str, str]:
        identity_user_id = str(uuid.uuid4())
        with db_session_factory() as db:
            db.add(
                ServiceDeskUser(
                    identity_user_id=identity_user_id,
                    email="test-service-desk-admin@utmn.ru",
                    display_name="Test Service Desk Admin",
                    access_type=ServiceDeskAccessType.SERVICE_DESK_ADMIN,
                    is_active=True,
                )
            )
            db.commit()

        admin_token = sign_platform_token(identity_user_id, permissions=["platform.admin"])
        return {"Authorization": f"Bearer {admin_token}"}

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield ServiceDeskTestClient(app, build_admin_headers)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers_for_user(db_session_factory):
    def build(user_id: str) -> dict[str, str]:
        with db_session_factory() as db:
            user = db.get(ServiceDeskUser, uuid.UUID(user_id))
            assert user is not None
            permissions = ["service_desk.access"]
            if user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
                permissions = ["platform.admin"]
            else:
                permissions.extend(item.capability for item in user.capabilities)
            token = sign_platform_token(user.identity_user_id, permissions=permissions)
        return {"Authorization": f"Bearer {token}"}

    return build
