"""add SLA pauses

Revision ID: 202607110019
Revises: 202607110018
"""
from alembic import op
import sqlalchemy as sa

revision = "202607110019"
down_revision = "202607110018"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("service_desk_sla_policies", sa.Column("pause_statuses", sa.JSON(), nullable=False, server_default="[]"))
    op.create_table("service_desk_ticket_sla_pauses",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("reason_status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_service_desk_ticket_sla_pauses_ticket_id", "service_desk_ticket_sla_pauses", ["ticket_id"])
    op.create_index("uq_service_desk_active_sla_pause", "service_desk_ticket_sla_pauses", ["ticket_id"], unique=True, postgresql_where=sa.text("ended_at IS NULL"), sqlite_where=sa.text("ended_at IS NULL"))

def downgrade() -> None:
    op.drop_index("uq_service_desk_active_sla_pause", table_name="service_desk_ticket_sla_pauses")
    op.drop_index("ix_service_desk_ticket_sla_pauses_ticket_id", table_name="service_desk_ticket_sla_pauses")
    op.drop_table("service_desk_ticket_sla_pauses")
    op.drop_column("service_desk_sla_policies", "pause_statuses")
