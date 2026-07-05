"""add user profile fields

Revision ID: 202607050002
Revises: 202607050001
Create Date: 2026-07-05 13:20:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607050002"
down_revision: str | None = "202607050001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("competencies", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("about", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "about")
    op.drop_column("users", "competencies")
