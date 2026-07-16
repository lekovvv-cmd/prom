"""initial service desk access schema

Revision ID: 202607090001
Revises:
Create Date: 2026-07-09 21:30:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607090001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("identity_user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("position", sa.String(length=255), nullable=True),
        sa.Column("access_type", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("identity_user_id"),
    )
    op.create_index(op.f("ix_service_desk_users_email"), "service_desk_users", ["email"], unique=False)
    op.create_index(
        op.f("ix_service_desk_users_identity_user_id"),
        "service_desk_users",
        ["identity_user_id"],
        unique=False,
    )

    op.create_table(
        "service_desk_user_capabilities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("service_desk_user_id", sa.Uuid(), nullable=False),
        sa.Column("capability", sa.String(length=128), nullable=False),
        sa.Column("scope_type", sa.String(length=64), nullable=True),
        sa.Column("scope_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["service_desk_user_id"], ["service_desk_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_user_capabilities_capability"),
        "service_desk_user_capabilities",
        ["capability"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_desk_user_capabilities_service_desk_user_id"),
        "service_desk_user_capabilities",
        ["service_desk_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_user_capabilities_service_desk_user_id"),
        table_name="service_desk_user_capabilities",
    )
    op.drop_index(
        op.f("ix_service_desk_user_capabilities_capability"),
        table_name="service_desk_user_capabilities",
    )
    op.drop_table("service_desk_user_capabilities")
    op.drop_index(op.f("ix_service_desk_users_identity_user_id"), table_name="service_desk_users")
    op.drop_index(op.f("ix_service_desk_users_email"), table_name="service_desk_users")
    op.drop_table("service_desk_users")
