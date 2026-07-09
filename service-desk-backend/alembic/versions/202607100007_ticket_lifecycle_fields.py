"""service desk ticket lifecycle fields

Revision ID: 202607100007
Revises: 202607100006
Create Date: 2026-07-10 01:30:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607100007"
down_revision: str | None = "202607100006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("service_desk_tickets", sa.Column("resolution_summary", sa.Text(), nullable=True))
    op.add_column("service_desk_tickets", sa.Column("cancellation_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("service_desk_tickets", "cancellation_reason")
    op.drop_column("service_desk_tickets", "resolution_summary")
