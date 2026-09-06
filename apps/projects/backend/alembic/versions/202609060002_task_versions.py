"""add optimistic concurrency versions to collaborative project tasks and stages

Revision ID: 202609060002
Revises: 202609060001
Create Date: 2026-09-06 00:02:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202609060002"
down_revision: str | None = "202609060001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_stages", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "project_tasks", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.alter_column("project_stages", "version", server_default=None)
    op.alter_column("project_tasks", "version", server_default=None)


def downgrade() -> None:
    op.drop_column("project_tasks", "version")
    op.drop_column("project_stages", "version")
