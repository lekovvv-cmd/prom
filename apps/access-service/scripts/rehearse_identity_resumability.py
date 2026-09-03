"""Exercise forward-only identity migration recovery on PostgreSQL.

This is deliberately a runtime rehearsal, rather than a unit-test-only hook: CI runs
it inside the migration container against all three PostgreSQL services.  The injected
callback is supplied directly to the application API and has no environment or CLI
switch, so normal production commands cannot accidentally activate it.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine, func, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from access_service.application.identity_migration import (
    IdentityMigrationApplyFailed,
    migrate_identities,
)
from access_service.domain.models import (
    AccessAuditEvent,
    Base,
    Group,
    GroupMembership,
    PlatformUser,
    Role,
    UserRoleAssignment,
)


def _required_url(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for the PostgreSQL rehearsal")
    return value


def _schema_url(database_url: str, schema: str) -> str:
    return (
        make_url(database_url)
        .update_query_dict({"options": f"-csearch_path={schema}"})
        .render_as_string(hide_password=False)
    )


def _create_schema(database_url: str, schema: str) -> str:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    finally:
        engine.dispose()
    return _schema_url(database_url, schema)


def _drop_schema(database_url: str, schema: str) -> None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    finally:
        engine.dispose()


def _create_legacy_tables(projects_engine: Engine, service_desk_engine: Engine) -> None:
    projects = MetaData()
    Table(
        "users",
        projects,
        Column("id", String(36), primary_key=True),
        Column("email", String(255), nullable=False),
        Column("full_name", String(255), nullable=False),
        Column("role", String(32), nullable=False),
        Column("department", String(255)),
        Column("position", String(255)),
        Column("external_subject", String(255)),
    )
    projects.create_all(projects_engine)

    service_desk = MetaData()
    Table(
        "service_desk_users",
        service_desk,
        Column("id", String(36), primary_key=True),
        Column("identity_user_id", String(64), nullable=False),
        Column("email", String(255), nullable=False),
        Column("display_name", String(255), nullable=False),
        Column("department", String(255)),
        Column("position", String(255)),
        Column("access_type", String(32), nullable=False),
        Column("is_active", Boolean, nullable=False),
        Column("external_subject", String(255)),
    )
    service_desk.create_all(service_desk_engine)


def _seed(
    *,
    projects_url: str,
    service_desk_url: str,
    access_url: str,
    canonical_id: str,
    old_access_id: str,
    projection_id: str,
    group_id: str,
) -> None:
    projects_engine = create_engine(projects_url)
    service_desk_engine = create_engine(service_desk_url)
    access_engine = create_engine(access_url)
    try:
        _create_legacy_tables(projects_engine, service_desk_engine)
        Base.metadata.create_all(access_engine)
        projects_users = Table("users", MetaData(), autoload_with=projects_engine)
        service_desk_users = Table(
            "service_desk_users", MetaData(), autoload_with=service_desk_engine
        )
        with projects_engine.begin() as connection:
            connection.execute(
                projects_users.insert().values(
                    id=canonical_id,
                    email="legacy.user@utmn.ru",
                    full_name="Legacy User",
                    role="project_manager",
                    department="SHPIU",
                    position="Manager",
                    external_subject="sso:legacy-user",
                )
            )
        with service_desk_engine.begin() as connection:
            connection.execute(
                service_desk_users.insert().values(
                    id=projection_id,
                    identity_user_id=old_access_id,
                    email="LEGACY.USER@UTMN.RU",
                    display_name="Legacy User",
                    department="SHPIU",
                    position="Manager",
                    access_type="service_desk_manager",
                    is_active=True,
                    external_subject="sso:legacy-user",
                )
            )
        with Session(access_engine) as session:
            session.add_all(
                [
                    PlatformUser(
                        id=old_access_id,
                        email="legacy.user@utmn.ru",
                        display_name="Old Access Name",
                        external_subject="sso:legacy-user",
                    ),
                    Group(id=group_id, code=f"legacy-{canonical_id}", title="Legacy"),
                    GroupMembership(group_id=group_id, user_id=old_access_id),
                    AccessAuditEvent(
                        actor_user_id=old_access_id,
                        action="legacy_action",
                        object_type="legacy",
                        object_id="legacy-object",
                        before=None,
                        after=None,
                        request_id=None,
                        source="identity-rehearsal",
                    ),
                ]
            )
            session.commit()
    finally:
        projects_engine.dispose()
        service_desk_engine.dispose()
        access_engine.dispose()


def _state(
    *, access_url: str, service_desk_url: str, canonical_id: str, projection_id: str
) -> dict[str, Any]:
    access_engine = create_engine(access_url)
    service_desk_engine = create_engine(service_desk_url)
    try:
        with Session(access_engine) as session:
            user = session.get(PlatformUser, canonical_id)
            assert user is not None
            roles = tuple(
                sorted(
                    session.scalars(
                        select(Role.code)
                        .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
                        .where(UserRoleAssignment.user_id == canonical_id)
                    ).all()
                )
            )
            migration_audits = tuple(
                sorted(
                    session.scalars(
                        select(AccessAuditEvent.action).where(
                            AccessAuditEvent.object_id == canonical_id,
                            AccessAuditEvent.source == "identity-migration",
                        )
                    ).all()
                )
            )
            access = {
                "users": session.scalar(select(func.count()).select_from(PlatformUser)),
                "email": user.email,
                "external_subject": user.external_subject,
                "session_version": user.session_version,
                "roles": roles,
                "memberships": session.scalar(
                    select(func.count())
                    .select_from(GroupMembership)
                    .where(GroupMembership.user_id == canonical_id)
                ),
                "legacy_actor_references": session.scalar(
                    select(func.count())
                    .select_from(AccessAuditEvent)
                    .where(
                        AccessAuditEvent.action == "legacy_action",
                        AccessAuditEvent.actor_user_id == canonical_id,
                    )
                ),
                "migration_audits": migration_audits,
            }
        service_desk_users = Table(
            "service_desk_users", MetaData(), autoload_with=service_desk_engine
        )
        with service_desk_engine.connect() as connection:
            projection = (
                connection.execute(
                    select(service_desk_users).where(service_desk_users.c.id == projection_id)
                )
                .mappings()
                .one()
            )
        return access | {
            "projection_identity_user_id": projection["identity_user_id"],
            "projection_email": projection["email"],
        }
    finally:
        access_engine.dispose()
        service_desk_engine.dispose()


def main() -> int:
    base_urls = {
        "projects": _required_url("PROJECTS_DATABASE_URL"),
        "service_desk": _required_url("SERVICE_DESK_DATABASE_URL"),
        "access": _required_url("ACCESS_DATABASE_URL"),
    }
    run_id = uuid.uuid4().hex
    schemas = {
        name: {flow: f"identity_rehearsal_{flow}_{run_id}" for flow in ("clean", "recovered")}
        for name in base_urls
    }
    urls = {
        name: {
            flow: _create_schema(database_url, schemas[name][flow])
            for flow in ("clean", "recovered")
        }
        for name, database_url in base_urls.items()
    }
    canonical_id, old_access_id, projection_id, group_id = (str(uuid.uuid4()) for _ in range(4))
    try:
        for flow in ("clean", "recovered"):
            _seed(
                projects_url=urls["projects"][flow],
                service_desk_url=urls["service_desk"][flow],
                access_url=urls["access"][flow],
                canonical_id=canonical_id,
                old_access_id=old_access_id,
                projection_id=projection_id,
                group_id=group_id,
            )

        with tempfile.TemporaryDirectory(prefix="identity-rehearsal-") as reports_root:
            reports = Path(reports_root)
            clean = migrate_identities(
                projects_database_url=urls["projects"]["clean"],
                service_desk_database_url=urls["service_desk"]["clean"],
                access_database_url=urls["access"]["clean"],
                apply=True,
                report_dir=reports / "clean",
            )
            assert clean["status"] == "completed"

            recovered_arguments = {
                "projects_database_url": urls["projects"]["recovered"],
                "service_desk_database_url": urls["service_desk"]["recovered"],
                "access_database_url": urls["access"]["recovered"],
                "apply": True,
                "report_dir": reports / "recovered",
            }
            try:
                migrate_identities(
                    **recovered_arguments,
                    after_access_commit=lambda: (_ for _ in ()).throw(
                        RuntimeError("injected failure after Access commit")
                    ),
                )
            except IdentityMigrationApplyFailed as exc:
                partial = exc.report
            else:
                raise AssertionError("failure injection did not interrupt Service Desk apply")

            assert partial["status"] == "partial"
            assert partial["applied"] is False
            assert partial["rerun_safe"] is True
            assert partial["phases"]["access"]["status"] == "completed"
            assert partial["phases"]["service_desk"] == {
                "status": "failed",
                "reason": "injected failure after Access commit",
            }
            saved_partial = json.loads(
                (reports / "recovered" / "identity-reconciliation.json").read_text(encoding="utf-8")
            )
            assert saved_partial["status"] == "partial"

            partial_state = _state(
                access_url=urls["access"]["recovered"],
                service_desk_url=urls["service_desk"]["recovered"],
                canonical_id=canonical_id,
                projection_id=projection_id,
            )
            assert partial_state["users"] == 1
            assert partial_state["email"] == "legacy.user@utmn.ru"
            assert partial_state["external_subject"] == "sso:legacy-user"
            assert partial_state["session_version"] == 2
            assert partial_state["roles"] == ("project_manager", "service_desk_manager")
            assert partial_state["memberships"] == 1
            assert partial_state["legacy_actor_references"] == 1
            assert partial_state["migration_audits"] == (
                "legacy_identity_migrated",
                "legacy_identity_rekeyed",
            )
            assert partial_state["projection_identity_user_id"] == old_access_id
            assert partial_state["projection_email"] == "LEGACY.USER@UTMN.RU"

            recovered = migrate_identities(**recovered_arguments)
            third_run = migrate_identities(**recovered_arguments)
            assert recovered["status"] == "completed"
            assert third_run["status"] == "completed"
            assert third_run["summary"]["actions"] == {"noop": 1}
            saved_completed = json.loads(
                (reports / "recovered" / "identity-reconciliation.json").read_text(encoding="utf-8")
            )
            assert saved_completed["status"] == "completed"

        clean_state = _state(
            access_url=urls["access"]["clean"],
            service_desk_url=urls["service_desk"]["clean"],
            canonical_id=canonical_id,
            projection_id=projection_id,
        )
        recovered_state = _state(
            access_url=urls["access"]["recovered"],
            service_desk_url=urls["service_desk"]["recovered"],
            canonical_id=canonical_id,
            projection_id=projection_id,
        )
        assert clean_state == recovered_state
        print("PostgreSQL identity migration resumability rehearsal passed.")
        return 0
    finally:
        for name, database_url in base_urls.items():
            for schema in schemas[name].values():
                _drop_schema(database_url, schema)


if __name__ == "__main__":
    raise SystemExit(main())
