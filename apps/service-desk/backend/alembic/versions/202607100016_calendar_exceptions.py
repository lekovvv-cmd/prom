"""add SLA calendar exceptions

Revision ID: 202607100016
Revises: 202607100015
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100016"
down_revision = "202607100015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_calendar_exceptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("calendar_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["calendar_id"], ["service_desk_business_calendars.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_calendar_exceptions_calendar_id"),
        "service_desk_calendar_exceptions",
        ["calendar_id"],
    )
    op.create_index(
        op.f("ix_service_desk_calendar_exceptions_date"),
        "service_desk_calendar_exceptions",
        ["date"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_calendar_exceptions_date"),
        table_name="service_desk_calendar_exceptions",
    )
    op.drop_index(
        op.f("ix_service_desk_calendar_exceptions_calendar_id"),
        table_name="service_desk_calendar_exceptions",
    )
    op.drop_table("service_desk_calendar_exceptions")
