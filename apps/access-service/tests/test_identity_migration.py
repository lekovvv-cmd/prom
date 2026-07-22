from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine, func, select
from sqlalchemy.orm import Session

from access_service.application.identity_migration import (
    IdentityMigrationConflict,
    migrate_identities,
)
from access_service.domain.models import Base, PlatformUser, Role, UserRoleAssignment


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
        projection = connection.execute(
            select(service_desk_users).where(service_desk_users.c.id == service_desk_user_id)
        ).mappings().one()
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
        connection.execute(
            service_desk_users.update().values(email="renamed.user@utmn.ru")
        )
    migrate_identities(**arguments)

    access_engine = create_engine(access_url)
    with Session(access_engine) as session:
        assert session.scalar(select(func.count()).select_from(PlatformUser)) == 1
        user = session.get(PlatformUser, user_id)
        assert user is not None
        assert user.email == "renamed.user@utmn.ru"
        assert user.external_subject == "sso:legacy-user"
        assert user.is_active is False


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

