"""service desk ticket number counters

Revision ID: 202607100006
Revises: 202607090005
Create Date: 2026-07-10 00:30:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607100006"
down_revision: str | None = "202607090005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_ticket_counters",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("last_value", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("year"),
    )


def downgrade() -> None:
    op.drop_table("service_desk_ticket_counters")
