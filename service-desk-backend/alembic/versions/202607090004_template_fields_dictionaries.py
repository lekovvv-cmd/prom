"""service desk template fields and dictionaries

Revision ID: 202607090004
Revises: 202607090003
Create Date: 2026-07-09 22:40:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607090004"
down_revision: str | None = "202607090003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_template_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_version_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("field_type", sa.String(length=32), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("help_text", sa.String(length=500), nullable=True),
        sa.Column("placeholder", sa.String(length=255), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("dictionary_code", sa.String(length=128), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("visibility_rules", sa.JSON(), nullable=True),
        sa.Column("required_rules", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_version_id"], ["service_desk_template_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_version_id", "key", name="uq_template_field_version_key"),
    )
    op.create_index(
        op.f("ix_service_desk_template_fields_template_version_id"),
        "service_desk_template_fields",
        ["template_version_id"],
        unique=False,
    )

    op.create_table(
        "service_desk_dictionaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_service_desk_dictionaries_code"), "service_desk_dictionaries", ["code"], unique=False)

    op.create_table(
        "service_desk_dictionary_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dictionary_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dictionary_id"], ["service_desk_dictionaries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_dictionary_items_dictionary_id"),
        "service_desk_dictionary_items",
        ["dictionary_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_dictionary_items_dictionary_id"),
        table_name="service_desk_dictionary_items",
    )
    op.drop_table("service_desk_dictionary_items")
    op.drop_index(op.f("ix_service_desk_dictionaries_code"), table_name="service_desk_dictionaries")
    op.drop_table("service_desk_dictionaries")
    op.drop_index(
        op.f("ix_service_desk_template_fields_template_version_id"),
        table_name="service_desk_template_fields",
    )
    op.drop_table("service_desk_template_fields")
