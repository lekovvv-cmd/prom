"""Remove capabilities implied by an active Service Desk role.

Revision ID: 202607120025
Revises: 202607120024
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607120025"
down_revision: str | None = "202607120024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM service_desk_user_capabilities "
        "WHERE capability IN ('service_desk.access', 'service_desk.create_request')"
    )


def downgrade() -> None:
    # Base access and request creation are role semantics and cannot be reconstructed per user.
    pass
