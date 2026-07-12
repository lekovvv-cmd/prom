"""Rename legacy demo identities without changing their source UUIDs.

Revision ID: 202607120003
Revises: 202607120002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607120003"
down_revision: str | None = "202607120002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET email = 'project.manager@utmn.ru' "
        "WHERE lower(email) = 'manager@utmn.ru'"
    )
    op.execute(
        "UPDATE users SET email = 'sd.manager@utmn.ru' "
        "WHERE lower(email) = 'analyst@utmn.ru'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET email = 'manager@utmn.ru' "
        "WHERE lower(email) = 'project.manager@utmn.ru'"
    )
    op.execute(
        "UPDATE users SET email = 'analyst@utmn.ru' "
        "WHERE lower(email) = 'sd.manager@utmn.ru'"
    )
