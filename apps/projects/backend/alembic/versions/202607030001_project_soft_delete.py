"""add project soft delete marker

Revision ID: 202607030001
Revises: 202607020002
Create Date: 2026-07-03 15:45:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607030001"
down_revision: str | None = "202607020002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_projects_deleted_at"), "projects", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_deleted_at"), table_name="projects")
    op.drop_column("projects", "deleted_at")
