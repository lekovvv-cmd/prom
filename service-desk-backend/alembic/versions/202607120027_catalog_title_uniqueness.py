"""Deduplicate catalog titles and enforce normalized scoped uniqueness.

Revision ID: 202607120027
Revises: 202607120026
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607120027"
down_revision: str | None = "202607120026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _deduplicate_categories(connection) -> None:
    while True:
        duplicate = connection.execute(
            sa.text(
                """
                SELECT duplicate.id AS duplicate_id, duplicate.canonical_id
                FROM (
                    SELECT id,
                           first_value(id) OVER (
                               PARTITION BY parent_id, lower(btrim(title))
                               ORDER BY created_at, id
                           ) AS canonical_id,
                           row_number() OVER (
                               PARTITION BY parent_id, lower(btrim(title))
                               ORDER BY created_at, id
                           ) AS duplicate_number
                    FROM service_desk_categories
                ) AS duplicate
                WHERE duplicate.duplicate_number > 1
                LIMIT 1
                """
            )
        ).mappings().first()
        if duplicate is None:
            return
        connection.execute(
            sa.text(
                "UPDATE service_desk_categories SET parent_id = :canonical "
                "WHERE parent_id = :duplicate"
            ),
            {"canonical": duplicate["canonical_id"], "duplicate": duplicate["duplicate_id"]},
        )
        connection.execute(
            sa.text(
                "UPDATE service_desk_services SET category_id = :canonical "
                "WHERE category_id = :duplicate"
            ),
            {"canonical": duplicate["canonical_id"], "duplicate": duplicate["duplicate_id"]},
        )
        connection.execute(
            sa.text("DELETE FROM service_desk_categories WHERE id = :duplicate"),
            {"duplicate": duplicate["duplicate_id"]},
        )


def _deduplicate_services(connection) -> None:
    while True:
        duplicate = connection.execute(
            sa.text(
                """
                SELECT duplicate.id AS duplicate_id, duplicate.canonical_id
                FROM (
                    SELECT id,
                           first_value(id) OVER (
                               PARTITION BY category_id, lower(btrim(title))
                               ORDER BY created_at, id
                           ) AS canonical_id,
                           row_number() OVER (
                               PARTITION BY category_id, lower(btrim(title))
                               ORDER BY created_at, id
                           ) AS duplicate_number
                    FROM service_desk_services
                ) AS duplicate
                WHERE duplicate.duplicate_number > 1
                LIMIT 1
                """
            )
        ).mappings().first()
        if duplicate is None:
            return
        max_version = connection.execute(
            sa.text(
                "SELECT coalesce(max(version), 0) FROM service_desk_template_versions "
                "WHERE service_id = :canonical"
            ),
            {"canonical": duplicate["canonical_id"]},
        ).scalar_one()
        versions = connection.execute(
            sa.text(
                "SELECT id FROM service_desk_template_versions "
                "WHERE service_id = :duplicate ORDER BY version, id"
            ),
            {"duplicate": duplicate["duplicate_id"]},
        ).scalars().all()
        for offset, version_id in enumerate(versions, start=1):
            connection.execute(
                sa.text(
                    "UPDATE service_desk_template_versions "
                    "SET service_id = :canonical, version = :version WHERE id = :version_id"
                ),
                {
                    "canonical": duplicate["canonical_id"],
                    "version": max_version + offset,
                    "version_id": version_id,
                },
            )
        connection.execute(
            sa.text(
                "UPDATE service_desk_tickets SET service_id = :canonical "
                "WHERE service_id = :duplicate"
            ),
            {"canonical": duplicate["canonical_id"], "duplicate": duplicate["duplicate_id"]},
        )
        connection.execute(
            sa.text("DELETE FROM service_desk_services WHERE id = :duplicate"),
            {"duplicate": duplicate["duplicate_id"]},
        )


def upgrade() -> None:
    connection = op.get_bind()
    _deduplicate_categories(connection)
    _deduplicate_services(connection)
    op.create_index(
        "uq_sd_categories_parent_normalized_title",
        "service_desk_categories",
        [sa.text("coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid)"), sa.text("lower(btrim(title))")],
        unique=True,
    )
    op.create_index(
        "uq_sd_services_category_normalized_title",
        "service_desk_services",
        ["category_id", sa.text("lower(btrim(title))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_sd_services_category_normalized_title",
        table_name="service_desk_services",
    )
    op.drop_index(
        "uq_sd_categories_parent_normalized_title",
        table_name="service_desk_categories",
    )
