"""add half year reports

Revision ID: 202607050003
Revises: 202607050002
Create Date: 2026-07-05 00:03:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607050003"
down_revision: str | None = "202607050002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_periods",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("opened_by", sa.Uuid(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["opened_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_periods_status"), "report_periods", ["status"], unique=False)
    op.create_table(
        "half_year_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("period_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("completed_work", sa.Text(), nullable=False),
        sa.Column("project_results", sa.Text(), nullable=True),
        sa.Column("competencies_used", sa.Text(), nullable=True),
        sa.Column("difficulties", sa.Text(), nullable=True),
        sa.Column("next_period_plans", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["period_id"], ["report_periods.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("period_id", "user_id", name="uq_half_year_report_period_user"),
    )
    op.create_index(op.f("ix_half_year_reports_period_id"), "half_year_reports", ["period_id"], unique=False)
    op.create_index(op.f("ix_half_year_reports_user_id"), "half_year_reports", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_half_year_reports_user_id"), table_name="half_year_reports")
    op.drop_index(op.f("ix_half_year_reports_period_id"), table_name="half_year_reports")
    op.drop_table("half_year_reports")
    op.drop_index(op.f("ix_report_periods_status"), table_name="report_periods")
    op.drop_table("report_periods")
