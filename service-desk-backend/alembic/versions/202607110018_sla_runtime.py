"""add SLA runtime state

Revision ID: 202607110018
Revises: 202607100017
"""
from alembic import op
import sqlalchemy as sa

revision = "202607110018"
down_revision = "202607100017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = (
        sa.Column("sla_policy_id", sa.Uuid(), nullable=True),
        sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_breached_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_breached_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_response_breached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_resolution_breached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("paused_seconds", sa.Integer(), nullable=False, server_default="0"),
    )
    for column in columns:
        op.add_column("service_desk_tickets", column)
    for name in ("sla_policy_id", "first_response_due_at", "resolution_due_at"):
        op.create_index(f"ix_service_desk_tickets_{name}", "service_desk_tickets", [name])


def downgrade() -> None:
    for name in ("resolution_due_at", "first_response_due_at", "sla_policy_id"):
        op.drop_index(f"ix_service_desk_tickets_{name}", table_name="service_desk_tickets")
    for name in ("paused_seconds", "is_resolution_breached", "is_response_breached", "resolution_breached_at", "response_breached_at", "first_response_at", "resolution_due_at", "first_response_due_at", "sla_policy_id"):
        op.drop_column("service_desk_tickets", name)
