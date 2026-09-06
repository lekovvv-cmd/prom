"""enforce a single active report period

Revision ID: 202609060003
Revises: 202609060002
Create Date: 2026-09-06 00:03:00
"""

from collections.abc import Sequence

from alembic import op


revision: str = "202609060003"
down_revision: str | None = "202609060002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Legacy data keeps the newest active period; historical ones become closed rather than deleted.
    op.execute(
        """
        WITH duplicates AS (
          SELECT id, row_number() OVER (ORDER BY opened_at DESC, id DESC) AS position
          FROM report_periods
          WHERE status = 'open'
        )
        UPDATE report_periods
        SET status = 'closed', closed_at = COALESCE(closed_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE id IN (SELECT id FROM duplicates WHERE position > 1)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_report_periods_one_open
        ON report_periods (status) WHERE status = 'open'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_report_periods_one_open")
