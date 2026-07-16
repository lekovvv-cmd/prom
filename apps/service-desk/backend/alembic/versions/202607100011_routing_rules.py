"""add routing rules

Revision ID: 202607100011
Revises: 202607100010
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100011"
down_revision = "202607100010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_routing_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("action", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_routing_rules_is_active"),
        "service_desk_routing_rules",
        ["is_active"],
    )
    op.create_index(
        op.f("ix_service_desk_routing_rules_priority"),
        "service_desk_routing_rules",
        ["priority"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_routing_rules_priority"),
        table_name="service_desk_routing_rules",
    )
    op.drop_index(
        op.f("ix_service_desk_routing_rules_is_active"),
        table_name="service_desk_routing_rules",
    )
    op.drop_table("service_desk_routing_rules")
