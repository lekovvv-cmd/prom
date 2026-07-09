"""service desk ticket drafts

Revision ID: 202607090005
Revises: 202607090004
Create Date: 2026-07-09 23:00:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607090005"
down_revision: str | None = "202607090004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=True),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("template_version_id", sa.Uuid(), nullable=False),
        sa.Column("requester_user_id", sa.Uuid(), nullable=False),
        sa.Column("assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("field_values", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_snapshot", sa.JSON(), nullable=True),
        sa.Column("routing_snapshot", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["requester_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["service_desk_services.id"]),
        sa.ForeignKeyConstraint(["template_version_id"], ["service_desk_template_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_index(op.f("ix_service_desk_tickets_assignee_user_id"), "service_desk_tickets", ["assignee_user_id"])
    op.create_index(op.f("ix_service_desk_tickets_number"), "service_desk_tickets", ["number"])
    op.create_index(op.f("ix_service_desk_tickets_priority"), "service_desk_tickets", ["priority"])
    op.create_index(op.f("ix_service_desk_tickets_requester_user_id"), "service_desk_tickets", ["requester_user_id"])
    op.create_index(op.f("ix_service_desk_tickets_service_id"), "service_desk_tickets", ["service_id"])
    op.create_index(op.f("ix_service_desk_tickets_status"), "service_desk_tickets", ["status"])

    op.create_table(
        "service_desk_ticket_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_desk_ticket_history_event_type"), "service_desk_ticket_history", ["event_type"])
    op.create_index(op.f("ix_service_desk_ticket_history_ticket_id"), "service_desk_ticket_history", ["ticket_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_ticket_history_ticket_id"), table_name="service_desk_ticket_history")
    op.drop_index(op.f("ix_service_desk_ticket_history_event_type"), table_name="service_desk_ticket_history")
    op.drop_table("service_desk_ticket_history")
    op.drop_index(op.f("ix_service_desk_tickets_status"), table_name="service_desk_tickets")
    op.drop_index(op.f("ix_service_desk_tickets_service_id"), table_name="service_desk_tickets")
    op.drop_index(op.f("ix_service_desk_tickets_requester_user_id"), table_name="service_desk_tickets")
    op.drop_index(op.f("ix_service_desk_tickets_priority"), table_name="service_desk_tickets")
    op.drop_index(op.f("ix_service_desk_tickets_number"), table_name="service_desk_tickets")
    op.drop_index(op.f("ix_service_desk_tickets_assignee_user_id"), table_name="service_desk_tickets")
    op.drop_table("service_desk_tickets")
