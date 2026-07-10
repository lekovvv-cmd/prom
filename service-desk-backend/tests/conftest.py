import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.main import create_app
from app.modules.access import models as access_models  # noqa: F401
from app.modules.access.models import ServiceDeskUser
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.routing import models as routing_models  # noqa: F401
from app.modules.templates import models as template_models  # noqa: F401
from app.modules.tickets import models as ticket_models  # noqa: F401


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers_for_user(db_session_factory):
    def build(user_id: str) -> dict[str, str]:
        with db_session_factory() as db:
            user = db.get(ServiceDeskUser, uuid.UUID(user_id))
            assert user is not None
            token = jwt.encode(
                {
                    "sub": user.identity_user_id,
                    "exp": datetime.now(UTC) + timedelta(minutes=5),
                },
                settings.jwt_secret,
                algorithm=settings.jwt_algorithm,
            )
        return {"Authorization": f"Bearer {token}"}

    return build
