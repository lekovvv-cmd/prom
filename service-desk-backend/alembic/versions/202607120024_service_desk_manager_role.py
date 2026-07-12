"""Rename the Service Desk manager access type.

Revision ID: 202607120024
Revises: 202607110023
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607120024"
down_revision: str | None = "202607110023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE service_desk_users SET access_type = 'service_desk_manager' "
        "WHERE access_type = 'manager'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE service_desk_users SET access_type = 'manager' "
        "WHERE access_type = 'service_desk_manager'"
    )
