from __future__ import annotations

from starlette.requests import Request
from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from access_service.api.router import (
    add_group_member,
    add_group_role,
    create_group,
    register_module,
    remove_group_member,
    upsert_role,
)
from access_service.api.schemas import GroupInput, ModuleInput, RoleInput
from access_service.application.access import modules_for_permissions, permissions_for
from access_service.application.catalog import ensure_access_catalog
from access_service.domain.models import Base, PlatformUser, Role, UserRoleAssignment


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
    result.state.request_id = "rbac-test"
    return result


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        ensure_access_catalog(db)
        roles = {role.code: role for role in db.scalars(select(Role)).all()}
        admin = PlatformUser(
            id="admin",
            email="admin@utmn.ru",
            display_name="Administrator",
        )
        employee = PlatformUser(
            id="employee",
            email="employee@utmn.ru",
            display_name="Employee",
        )
        admin.assignments.append(UserRoleAssignment(role=roles["platform_admin"]))
        db.add_all([admin, employee])
        db.commit()
        yield db
    engine.dispose()


def test_group_roles_are_effective_and_membership_revokes_session(session: Session) -> None:
    admin = session.get(PlatformUser, "admin")
    employee = session.get(PlatformUser, "employee")
    assert admin is not None and employee is not None
    group = create_group(
        GroupInput(code="project-managers", title="Project managers"),
        request(),
        admin,
        session,
    )
    initial_version = employee.session_version
    add_group_member(group.id, employee.id, request(), admin, session)
    role = session.scalar(select(Role).where(Role.code == "project_manager"))
    assert role is not None
    add_group_role(group.id, role.id, request(), admin, session)
    session.refresh(employee)

    effective = permissions_for(session, employee)
    assert "projects.create" in effective
    assert "projects.access" in effective
    assert employee.session_version == initial_version + 2
    modules = modules_for_permissions(session, effective)
    assert [module["id"] for module in modules] == ["projects"]


def test_duplicate_membership_is_rejected(session: Session) -> None:
    admin = session.get(PlatformUser, "admin")
    employee = session.get(PlatformUser, "employee")
    assert admin is not None and employee is not None
    group = create_group(
        GroupInput(code="employees", title="Employees"),
        request(),
        admin,
        session,
    )
    add_group_member(group.id, employee.id, request(), admin, session)
    with pytest.raises(HTTPException) as error:
        add_group_member(group.id, employee.id, request(), admin, session)
    assert error.value.status_code == 409


def test_last_admin_cannot_be_removed_from_admin_group(session: Session) -> None:
    admin = session.get(PlatformUser, "admin")
    assert admin is not None
    admin.assignments.clear()
    session.commit()
    group = create_group(
        GroupInput(code="platform-admins", title="Platform administrators"),
        request(),
        admin,
        session,
    )
    add_group_member(group.id, admin.id, request(), admin, session)
    role = session.scalar(select(Role).where(Role.code == "platform_admin"))
    assert role is not None
    add_group_role(group.id, role.id, request(), admin, session)

    with pytest.raises(HTTPException) as error:
        remove_group_member(group.id, admin.id, request(), admin, session)
    assert error.value.status_code == 409
    session.rollback()


def test_temporary_module_is_dynamic_and_role_integrity_is_enforced(session: Session) -> None:
    admin = session.get(PlatformUser, "admin")
    employee = session.get(PlatformUser, "employee")
    assert admin is not None and employee is not None
    registered = register_module(
        ModuleInput(id="documents", title="Documents"),
        request(),
        admin,
        session,
    )
    assert registered.id == "documents"
    documents_role = upsert_role(
        RoleInput(
            code="documents_editor",
            title="Documents editor",
            module_id="documents",
            permissions=["documents.access"],
        ),
        request(),
        admin,
        session,
    )
    session.add(UserRoleAssignment(user_id=employee.id, role_id=documents_role.id))
    session.commit()
    effective = permissions_for(session, employee)
    assert effective == {"documents.access"}
    assert modules_for_permissions(session, effective) == [
        {"id": "documents", "permissions": ["documents.access"]}
    ]

    with pytest.raises(HTTPException) as error:
        upsert_role(
            RoleInput(
                code="invalid_cross_module",
                title="Invalid cross module role",
                module_id="projects",
                permissions=["service_desk.access"],
            ),
            request(),
            admin,
            session,
        )
    assert error.value.status_code == 422

