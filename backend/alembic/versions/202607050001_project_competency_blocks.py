"""add project competency blocks

Revision ID: 202607050001
Revises: 202607030002
Create Date: 2026-07-05 11:40:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607050001"
down_revision: str | None = "202607030002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("competency_blocks", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "competency_blocks")
