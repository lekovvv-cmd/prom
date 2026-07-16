"""Rename the platform admin role.

Revision ID: 202607120002
Revises: 202607060001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607120002"
down_revision: str | None = "202607060001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'platform_admin' WHERE role = 'admin'")


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'admin' WHERE role = 'platform_admin'")
