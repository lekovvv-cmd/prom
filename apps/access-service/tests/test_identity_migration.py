from __future__ import annotations

import argparse
import importlib.util
import uuid
from pathlib import Path

import pytest
from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine, func, select
from sqlalchemy.orm import Session

from access_service.application.identity_migration import (
    IdentityMigrationApplyFailed,
    IdentityMigrationConflict,
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
from access_service.bootstrap.config import AccessSettings
from access_service.infrastructure.identity import InternalTokenSigner


def database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def legacy_databases(tmp_path: Path) -> tuple[str, str, str, Table, Table]:
    projects_url = database_url(tmp_path / "projects.db")
    service_desk_url = database_url(tmp_path / "service-desk.db")
    access_url = database_url(tmp_path / "access.db")

    projects_engine = create_engine(projects_url)
    projects_metadata = MetaData()
    projects_users = Table(
        "users",
        projects_metadata,
        Column("id", String(36), primary_key=True),
        Column("email", String(255), nullable=False),
        Column("full_name", String(255), nullable=False),
        Column("role", String(32), nullable=False),
        Column("department", String(255)),
        Column("position", String(255)),
        Column("external_subject", String(255)),
    )
    projects_metadata.create_all(projects_engine)
    projects_engine.dispose()

    service_desk_engine = create_engine(service_desk_url)
    service_desk_metadata = MetaData()
    service_desk_users = Table(
        "service_desk_users",
        service_desk_metadata,
        Column("id", String(36), primary_key=True),
        Column("identity_user_id", String(64), nullable=False),
        Column("email", String(255), nullable=False),
        Column("display_name", String(255), nullable=False),
        Column("department", String(255)),
        Column("position", String(255)),
        Column("access_type", String(32), nullable=False),
        Column("is_active", Boolean, nullable=False, default=True),
        Column("external_subject", String(255)),
    )
    service_desk_metadata.create_all(service_desk_engine)
    service_desk_engine.dispose()

    access_engine = create_engine(access_url)
    Base.metadata.create_all(access_engine)
    access_engine.dispose()
    return projects_url, service_desk_url, access_url, projects_users, service_desk_users


def insert_legacy_user(
    *,
    projects_url: str,
    service_desk_url: str,
    projects_users: Table,
    service_desk_users: Table,
    project_user_id: str,
    access_projection_id: str,
    email: str = "legacy.user@utmn.ru",
    active: bool = True,
    external_subject: str | None = "sso:legacy-user",
) -> str:
    service_desk_user_id = str(uuid.uuid4())
    with create_engine(projects_url).begin() as connection:
        connection.execute(
            projects_users.insert().values(
                id=project_user_id,
                email=email,
                full_name="Legacy User",
                role="project_manager",
                department="SHPIU",
                position="Manager",
                external_subject=external_subject,
            )
        )
    with create_engine(service_desk_url).begin() as connection:
        connection.execute(
            service_desk_users.insert().values(
                id=service_desk_user_id,
                identity_user_id=access_projection_id,
                email=email.upper(),
                display_name="Legacy User",
                department="SHPIU",
                position="Manager",
                access_type="service_desk_manager",
                is_active=active,
                external_subject=external_subject,
            )
        )
    return service_desk_user_id


def test_dry_run_does_not_mutate_and_apply_preserves_projects_uuid(tmp_path: Path) -> None:
    projects_url, service_desk_url, access_url, projects_users, service_desk_users = (
        legacy_databases(tmp_path)
    )
    project_user_id = str(uuid.uuid4())
    old_access_id = str(uuid.uuid4())
    service_desk_user_id = insert_legacy_user(
        projects_url=projects_url,
        service_desk_url=service_desk_url,
        projects_users=projects_users,
        service_desk_users=service_desk_users,
        project_user_id=project_user_id,
        access_projection_id=old_access_id,
    )
    access_engine = create_engine(access_url)
    with Session(access_engine) as session:
        session.add(
            PlatformUser(
                id=old_access_id,
                email="legacy.user@utmn.ru",
                display_name="Old Access Name",
                external_subject="sso:legacy-user",
            )
        )
        session.commit()

    dry_run = migrate_identities(
        projects_database_url=projects_url,
        service_desk_database_url=service_desk_url,
        access_database_url=access_url,
        apply=False,
        report_dir=tmp_path / "dry-run-report",
    )
    assert dry_run["can_apply"] is True
    assert dry_run["identities"][0]["action"] == "rekey"
    with Session(access_engine) as session:
        assert session.get(PlatformUser, old_access_id) is not None
        assert session.get(PlatformUser, project_user_id) is None

    applied = migrate_identities(
        projects_database_url=projects_url,
        service_desk_database_url=service_desk_url,
        access_database_url=access_url,
        apply=True,
        report_dir=tmp_path / "apply-report",
    )
    assert applied["applied"] is True
    assert (tmp_path / "apply-report" / "identity-reconciliation.json").is_file()
    assert (tmp_path / "apply-report" / "identity-reconciliation.md").is_file()
    with Session(access_engine) as session:
        user = session.get(PlatformUser, project_user_id)
        assert user is not None
        assert user.external_subject == "sso:legacy-user"
        assert user.email == "legacy.user@utmn.ru"
        assert session.get(PlatformUser, old_access_id) is None
        role_codes = set(
            session.scalars(
                select(Role.code)
                .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
                .where(UserRoleAssignment.user_id == project_user_id)
            ).all()
        )
        assert role_codes == {"project_manager", "service_desk_manager"}
    with create_engine(service_desk_url).connect() as connection:
        projection = (
            connection.execute(
                select(service_desk_users).where(service_desk_users.c.id == service_desk_user_id)
            )
            .mappings()
            .one()
        )
        assert projection["identity_user_id"] == project_user_id
        assert projection["email"] == "legacy.user@utmn.ru"


def test_apply_is_idempotent_and_email_change_keeps_identity(tmp_path: Path) -> None:
    projects_url, service_desk_url, access_url, projects_users, service_desk_users = (
        legacy_databases(tmp_path)
    )
    user_id = str(uuid.uuid4())
    insert_legacy_user(
        projects_url=projects_url,
        service_desk_url=service_desk_url,
        projects_users=projects_users,
        service_desk_users=service_desk_users,
        project_user_id=user_id,
        access_projection_id=str(uuid.uuid4()),
        active=False,
    )
    arguments = {
        "projects_database_url": projects_url,
        "service_desk_database_url": service_desk_url,
        "access_database_url": access_url,
        "apply": True,
        "report_dir": tmp_path / "report",
    }
    migrate_identities(**arguments)
    migrate_identities(**arguments)

    projects_engine = create_engine(projects_url)
    service_desk_engine = create_engine(service_desk_url)
    with projects_engine.begin() as connection:
        connection.execute(
            projects_users.update()
            .where(projects_users.c.id == user_id)
            .values(email="renamed.user@utmn.ru")
        )
    with service_desk_engine.begin() as connection:
        connection.execute(service_desk_users.update().values(email="renamed.user@utmn.ru"))
    migrate_identities(**arguments)

    access_engine = create_engine(access_url)
    with Session(access_engine) as session:
        assert session.scalar(select(func.count()).select_from(PlatformUser)) == 1
        user = session.get(PlatformUser, user_id)
        assert user is not None
        assert user.email == "renamed.user@utmn.ru"
        assert user.external_subject == "sso:legacy-user"
        assert user.is_active is False


def _identity_state(
    *,
    access_url: str,
    service_desk_url: str,
    service_desk_users: Table,
    user_id: str,
    service_desk_user_id: str,
) -> tuple[object, ...]:
    with Session(create_engine(access_url)) as session:
        user = session.get(PlatformUser, user_id)
        assert user is not None
        roles = tuple(sorted(assignment.role.code for assignment in user.assignments))
        memberships = session.scalar(
            select(func.count())
            .select_from(GroupMembership)
            .where(GroupMembership.user_id == user_id)
        )
        audits = tuple(
            sorted(
                session.scalars(
                    select(AccessAuditEvent.action).where(
                        AccessAuditEvent.object_id == user_id,
                        AccessAuditEvent.source == "identity-migration",
                    )
                ).all()
            )
        )
        access = (
            session.scalar(select(func.count()).select_from(PlatformUser)),
            user.id,
            user.email,
            user.external_subject,
            user.session_version,
            roles,
            memberships,
            audits,
        )
    with create_engine(service_desk_url).connect() as connection:
        projection = (
            connection.execute(
                select(service_desk_users).where(service_desk_users.c.id == service_desk_user_id)
            )
            .mappings()
            .one()
        )
        service_desk = (projection["identity_user_id"], projection["email"])
    return access + service_desk


def test_partial_access_commit_is_reported_and_rerun_converges_rekey(
    tmp_path: Path,
) -> None:
    canonical_id = str(uuid.uuid4())
    old_access_id = str(uuid.uuid4())

    def setup(root: Path) -> tuple[str, str, str, Table, str, str]:
        root.mkdir()
        projects_url, service_desk_url, access_url, projects_users, service_desk_users = (
            legacy_databases(root)
        )
        projection_id = insert_legacy_user(
            projects_url=projects_url,
            service_desk_url=service_desk_url,
            projects_users=projects_users,
            service_desk_users=service_desk_users,
            project_user_id=canonical_id,
            access_projection_id=old_access_id,
        )
        with Session(create_engine(access_url)) as session:
            group = Group(id=str(uuid.uuid4()), code=f"legacy-{canonical_id}", title="Legacy")
            session.add(
                PlatformUser(
                    id=old_access_id,
                    email="legacy.user@utmn.ru",
                    display_name="Old Access Name",
                    external_subject="sso:legacy-user",
                )
            )
            session.add_all(
                [
                    group,
                    GroupMembership(group_id=group.id, user_id=old_access_id),
                    AccessAuditEvent(
                        actor_user_id=old_access_id,
                        action="legacy_action",
                        object_type="legacy",
                        object_id="legacy-object",
                        before=None,
                        after=None,
                        request_id=None,
                        source="legacy-test",
                    ),
                ]
            )
            session.commit()
        return (
            projects_url,
            service_desk_url,
            access_url,
            service_desk_users,
            canonical_id,
            projection_id,
        )

    clean = setup(tmp_path / "clean")
    recovered = setup(tmp_path / "recovered")
    clean_arguments = {
        "projects_database_url": clean[0],
        "service_desk_database_url": clean[1],
        "access_database_url": clean[2],
        "apply": True,
        "report_dir": tmp_path / "clean-report",
    }
    assert migrate_identities(**clean_arguments)["status"] == "completed"

    recovered_arguments = {
        "projects_database_url": recovered[0],
        "service_desk_database_url": recovered[1],
        "access_database_url": recovered[2],
        "apply": True,
        "report_dir": tmp_path / "recovered-report",
    }

    with pytest.raises(IdentityMigrationApplyFailed) as failed:
        migrate_identities(
            **recovered_arguments,
            after_access_commit=lambda: (_ for _ in ()).throw(
                RuntimeError("injected failure after Access commit")
            ),
        )

    partial = failed.value.report
    assert partial["status"] == "partial"
    assert partial["applied"] is False
    assert partial["rerun_safe"] is True
    assert partial["phases"] == {
        "reconciliation": {"status": "completed", "reason": None},
        "access": {"status": "completed", "reason": None},
        "service_desk": {
            "status": "failed",
            "reason": "injected failure after Access commit",
        },
    }
    assert partial["failure"] == {
        "phase": "service_desk",
        "reason": "injected failure after Access commit",
    }
    report_json = (tmp_path / "recovered-report" / "identity-reconciliation.json").read_text(
        encoding="utf-8"
    )
    report_markdown = (tmp_path / "recovered-report" / "identity-reconciliation.md").read_text(
        encoding="utf-8"
    )
    assert '"status": "partial"' in report_json
    assert "| service_desk | failed | injected failure after Access commit |" in report_markdown

    with Session(create_engine(recovered[2])) as session:
        canonical = session.get(PlatformUser, recovered[4])
        assert canonical is not None
        assert canonical.external_subject == "sso:legacy-user"
        assert canonical.session_version == 2
        assert session.scalar(select(func.count()).select_from(PlatformUser)) == 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(GroupMembership)
                .where(GroupMembership.user_id == recovered[4])
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(AccessAuditEvent)
                .where(
                    AccessAuditEvent.action == "legacy_action",
                    AccessAuditEvent.actor_user_id == recovered[4],
                )
            )
            == 1
        )
    with create_engine(recovered[1]).connect() as connection:
        partial_projection = (
            connection.execute(select(recovered[3]).where(recovered[3].c.id == recovered[5]))
            .mappings()
            .one()
        )
        assert partial_projection["identity_user_id"] != recovered[4]
        assert partial_projection["email"] == "LEGACY.USER@UTMN.RU"

    rerun = migrate_identities(**recovered_arguments)
    third_run = migrate_identities(**recovered_arguments)
    assert rerun["status"] == "completed"
    assert third_run["status"] == "completed"
    assert third_run["summary"]["actions"] == {"noop": 1}
    assert _identity_state(
        access_url=recovered[2],
        service_desk_url=recovered[1],
        service_desk_users=recovered[3],
        user_id=recovered[4],
        service_desk_user_id=recovered[5],
    )[7] == ("legacy_identity_migrated", "legacy_identity_rekeyed")

    assert _identity_state(
        access_url=clean[2],
        service_desk_url=clean[1],
        service_desk_users=clean[3],
        user_id=clean[4],
        service_desk_user_id=clean[5],
    ) == _identity_state(
        access_url=recovered[2],
        service_desk_url=recovered[1],
        service_desk_users=recovered[3],
        user_id=recovered[4],
        service_desk_user_id=recovered[5],
    )


def test_cli_returns_nonzero_and_names_report_for_partial_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    script_path = Path(__file__).parents[1] / "scripts" / "migrate_identities.py"
    spec = importlib.util.spec_from_file_location("identity_migration_cli", script_path)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(
        cli,
        "parse_args",
        lambda: argparse.Namespace(
            projects_database_url="projects",
            service_desk_database_url="service-desk",
            access_database_url="access",
            apply=True,
            report_dir=report_dir,
        ),
    )

    def fail_after_access_commit(**_: object) -> None:
        raise IdentityMigrationApplyFailed(
            phase="service_desk",
            reason="injected failure after Access commit",
            report={"status": "partial"},
        )

    monkeypatch.setattr(cli, "migrate_identities", fail_after_access_commit)
    assert cli.main() == 1
    output = capsys.readouterr().out
    assert "partial: phase=service_desk" in output
    assert "injected failure after Access commit" in output
    assert str(report_dir.resolve()) in output


def test_duplicate_normalized_email_blocks_apply(tmp_path: Path) -> None:
    projects_url, service_desk_url, access_url, projects_users, _ = legacy_databases(tmp_path)
    with create_engine(projects_url).begin() as connection:
        connection.execute(
            projects_users.insert(),
            [
                {
                    "id": str(uuid.uuid4()),
                    "email": "duplicate@utmn.ru",
                    "full_name": "First",
                    "role": "employee",
                },
                {
                    "id": str(uuid.uuid4()),
                    "email": " DUPLICATE@UTMN.RU ",
                    "full_name": "Second",
                    "role": "employee",
                },
            ],
        )
    with pytest.raises(IdentityMigrationConflict):
        migrate_identities(
            projects_database_url=projects_url,
            service_desk_database_url=service_desk_url,
            access_database_url=access_url,
            apply=True,
            report_dir=tmp_path / "report",
        )
    with Session(create_engine(access_url)) as session:
        assert session.scalar(select(func.count()).select_from(PlatformUser)) == 0


def test_clear_uuid_conflict_blocks_apply(tmp_path: Path) -> None:
    projects_url, service_desk_url, access_url, projects_users, service_desk_users = (
        legacy_databases(tmp_path)
    )
    desired_id = str(uuid.uuid4())
    existing_email_id = str(uuid.uuid4())
    insert_legacy_user(
        projects_url=projects_url,
        service_desk_url=service_desk_url,
        projects_users=projects_users,
        service_desk_users=service_desk_users,
        project_user_id=desired_id,
        access_projection_id=existing_email_id,
        external_subject=None,
    )
    access_engine = create_engine(access_url)
    with Session(access_engine) as session:
        session.add_all(
            [
                PlatformUser(
                    id=desired_id,
                    email="different.user@utmn.ru",
                    display_name="Different UUID owner",
                ),
                PlatformUser(
                    id=existing_email_id,
                    email="legacy.user@utmn.ru",
                    display_name="Email owner",
                ),
            ]
        )
        session.commit()
    with pytest.raises(IdentityMigrationConflict):
        migrate_identities(
            projects_database_url=projects_url,
            service_desk_database_url=service_desk_url,
            access_database_url=access_url,
            apply=True,
            report_dir=tmp_path / "report",
        )


def test_migrated_identity_keeps_all_legacy_relationships_and_token_subject(
    tmp_path: Path,
) -> None:
    projects_url, service_desk_url, access_url, projects_users, service_desk_users = (
        legacy_databases(tmp_path)
    )
    user_id = str(uuid.uuid4())
    insert_legacy_user(
        projects_url=projects_url,
        service_desk_url=service_desk_url,
        projects_users=projects_users,
        service_desk_users=service_desk_users,
        project_user_id=user_id,
        access_projection_id=str(uuid.uuid4()),
    )
    projects_metadata = MetaData()
    relationships = [
        Table(
            table_name,
            projects_metadata,
            Column("id", String(36), primary_key=True),
            Column("user_id", String(36), nullable=False),
        )
        for table_name in ("projects", "project_responses", "project_tasks", "half_year_reports")
    ]
    projects_engine = create_engine(projects_url)
    projects_metadata.create_all(projects_engine)
    with projects_engine.begin() as connection:
        for table in relationships:
            connection.execute(table.insert().values(id=str(uuid.uuid4()), user_id=user_id))
    tickets_metadata = MetaData()
    tickets = Table(
        "service_desk_tickets",
        tickets_metadata,
        Column("id", String(36), primary_key=True),
        Column("requester_user_id", String(36), nullable=False),
    )
    service_desk_engine = create_engine(service_desk_url)
    tickets_metadata.create_all(service_desk_engine)
    with service_desk_engine.begin() as connection:
        connection.execute(tickets.insert().values(id=str(uuid.uuid4()), requester_user_id=user_id))

    migrate_identities(
        projects_database_url=projects_url,
        service_desk_database_url=service_desk_url,
        access_database_url=access_url,
        apply=True,
        report_dir=tmp_path / "report",
    )

    with projects_engine.connect() as connection:
        assert {connection.scalar(select(table.c.user_id)) for table in relationships} == {user_id}
    with service_desk_engine.connect() as connection:
        assert connection.scalar(select(tickets.c.requester_user_id)) == user_id
    with Session(create_engine(access_url)) as session:
        migrated = session.get(PlatformUser, user_id)
        assert migrated is not None
        role_codes = {assignment.role.code for assignment in migrated.assignments}
    signer = InternalTokenSigner(AccessSettings(database_url=access_url))
    token = signer.issue(
        user_id=user_id,
        external_subject=migrated.external_subject,
        email=migrated.email,
        display_name=migrated.display_name,
        permissions={"projects.access", "service_desk.access"},
        session_version=migrated.session_version,
    )

    assert role_codes == {"project_manager", "service_desk_manager"}
    assert signer.verify(token, audience="projects")["sub"] == user_id
    assert signer.verify(token, audience="service-desk")["sub"] == user_id
