from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from access_service.api.router import add_group_member, add_group_role, create_group
from access_service.api.schemas import GroupInput
from access_service.application.access import permissions_for
from access_service.application.catalog import ensure_access_catalog
from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import PlatformUser, Role, UserRoleAssignment
from access_service.infrastructure.identity import DatabaseSigningKeyStore


POSTGRES_URL = os.getenv("ACCESS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Access PostgreSQL integration contour is disabled",
)


def request() -> Request:
    result = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "client": ("127.0.0.1", 5000),
            "server": ("test", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )
    result.state.request_id = "postgres-integration"
    return result


def test_postgres_group_rbac_and_persisted_key_rotation() -> None:
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    suffix = uuid.uuid4().hex

    with session_factory() as session:
        assert session.bind is not None
        assert session.bind.dialect.name == "postgresql"
        ensure_access_catalog(session)
        roles = {role.code: role for role in session.scalars(select(Role)).all()}
        admin = PlatformUser(
            id=str(uuid.uuid4()),
            email=f"admin-{suffix}@utmn.ru",
            display_name="PostgreSQL Admin",
        )
        employee = PlatformUser(
            id=str(uuid.uuid4()),
            email=f"employee-{suffix}@utmn.ru",
            display_name="PostgreSQL Employee",
        )
        admin.assignments.append(UserRoleAssignment(role=roles["platform_admin"]))
        employee.assignments.append(UserRoleAssignment(role=roles["employee"]))
        session.add_all([admin, employee])
        session.commit()

        group = create_group(
            GroupInput(code=f"managers-{suffix}", title="Managers"),
            request(),
            admin,
            session,
        )
        add_group_member(group.id, employee.id, request(), admin, session)
        add_group_role(
            group.id,
            roles["project_manager"].id,
            request(),
            admin,
            session,
        )
        session.refresh(employee)
        effective = permissions_for(session, employee)
        assert "projects.respond" in effective
        assert "projects.create" in effective
        assert employee.session_version == 3

    settings = AccessSettings(
        database_url=POSTGRES_URL,
        jwt_key_id=f"initial-{suffix}",
    )
    key_store = DatabaseSigningKeyStore(settings, session_factory)
    initial_kid = key_store.active().kid
    rotated_kid = f"rotated-{suffix}"
    key_store.rotate(kid=rotated_kid)

    assert key_store.active().kid == rotated_kid
    assert {key.kid for key in key_store.verification_keys()} == {
        initial_kid,
        rotated_kid,
    }

    engine.dispose()
