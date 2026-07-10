"""add SLA escalation rules and events

Revision ID: 202607110020
Revises: 202607110019
"""
from alembic import op
import sqlalchemy as sa

revision = "202607110020"
down_revision = "202607110019"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("service_desk_escalation_rules",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("sla_policy_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.String(32), nullable=False), sa.Column("threshold_percent", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False), sa.Column("recipient_type", sa.String(32), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=True), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["sla_policy_id"], ["service_desk_sla_policies.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["service_desk_users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_service_desk_escalation_rules_sla_policy_id", "service_desk_escalation_rules", ["sla_policy_id"])
    op.create_table("service_desk_sla_escalation_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False), sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False), sa.Column("recipient_type", sa.String(32), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.ForeignKeyConstraint(["rule_id"], ["service_desk_escalation_rules.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("ticket_id", "rule_id", name="uq_sla_escalation_ticket_rule"))
    op.create_index("ix_service_desk_sla_escalation_events_ticket_id", "service_desk_sla_escalation_events", ["ticket_id"])

def downgrade() -> None:
    op.drop_index("ix_service_desk_sla_escalation_events_ticket_id", table_name="service_desk_sla_escalation_events")
    op.drop_table("service_desk_sla_escalation_events")
    op.drop_index("ix_service_desk_escalation_rules_sla_policy_id", table_name="service_desk_escalation_rules")
    op.drop_table("service_desk_escalation_rules")
