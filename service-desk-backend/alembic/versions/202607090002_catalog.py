"""service desk catalog

Revision ID: 202607090002
Revises: 202607090001
Create Date: 2026-07-09 22:00:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607090002"
down_revision: str | None = "202607090001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["service_desk_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_categories_title"),
        "service_desk_categories",
        ["title"],
        unique=False,
    )

    op.create_table(
        "service_desk_services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["service_desk_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_services_category_id"),
        "service_desk_services",
        ["category_id"],
        unique=False,
    )
    op.create_index(op.f("ix_service_desk_services_title"), "service_desk_services", ["title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_services_title"), table_name="service_desk_services")
    op.drop_index(op.f("ix_service_desk_services_category_id"), table_name="service_desk_services")
    op.drop_table("service_desk_services")
    op.drop_index(op.f("ix_service_desk_categories_title"), table_name="service_desk_categories")
    op.drop_table("service_desk_categories")
