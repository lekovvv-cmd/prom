"""add SLA policies and bindings

Revision ID: 202607100017
Revises: 202607100016
Create Date: 2026-07-11
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100017"
down_revision = "202607100016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_sla_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("business_calendar_id", sa.Uuid(), nullable=False),
        sa.Column("first_response_minutes", sa.Integer(), nullable=False),
        sa.Column("resolution_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_calendar_id"], ["service_desk_business_calendars.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_sla_policies_is_active"),
        "service_desk_sla_policies",
        ["is_active"],
    )
    op.create_table(
        "service_desk_sla_bindings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["service_desk_sla_policies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_sla_bindings_is_active"),
        "service_desk_sla_bindings",
        ["is_active"],
    )
    op.create_index(
        op.f("ix_service_desk_sla_bindings_policy_id"),
        "service_desk_sla_bindings",
        ["policy_id"],
    )
    op.create_index(
        op.f("ix_service_desk_sla_bindings_priority"),
        "service_desk_sla_bindings",
        ["priority"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_sla_bindings_priority"),
        table_name="service_desk_sla_bindings",
    )
    op.drop_index(
        op.f("ix_service_desk_sla_bindings_policy_id"),
        table_name="service_desk_sla_bindings",
    )
    op.drop_index(
        op.f("ix_service_desk_sla_bindings_is_active"),
        table_name="service_desk_sla_bindings",
    )
    op.drop_table("service_desk_sla_bindings")
    op.drop_index(
        op.f("ix_service_desk_sla_policies_is_active"),
        table_name="service_desk_sla_policies",
    )
    op.drop_table("service_desk_sla_policies")
