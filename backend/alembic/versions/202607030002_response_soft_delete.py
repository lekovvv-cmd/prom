"""add response soft delete marker

Revision ID: 202607030002
Revises: 202607030001
Create Date: 2026-07-03 17:30:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607030002"
down_revision: str | None = "202607030001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("project_responses", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_project_responses_deleted_at"), "project_responses", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_responses_deleted_at"), table_name="project_responses")
    op.drop_column("project_responses", "deleted_at")
