"""add SLA business calendars

Revision ID: 202607100015
Revises: 202607100014
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100015"
down_revision = "202607100014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_business_calendars",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_business_calendars_is_active"),
        "service_desk_business_calendars",
        ["is_active"],
    )
    op.create_table(
        "service_desk_business_hours",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("calendar_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(["calendar_id"], ["service_desk_business_calendars.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_business_hours_calendar_id"),
        "service_desk_business_hours",
        ["calendar_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_business_hours_calendar_id"), table_name="service_desk_business_hours")
    op.drop_table("service_desk_business_hours")
    op.drop_index(
        op.f("ix_service_desk_business_calendars_is_active"),
        table_name="service_desk_business_calendars",
    )
    op.drop_table("service_desk_business_calendars")
