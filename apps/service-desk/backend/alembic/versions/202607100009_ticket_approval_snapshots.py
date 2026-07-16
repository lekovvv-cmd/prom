"""service desk ticket approval snapshots

Revision ID: 202607100009
Revises: 202607100008
Create Date: 2026-07-10 04:20:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607100009"
down_revision: str | None = "202607100008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_ticket_approval_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("decision_rule", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticket_id",
            "position",
            name="uq_sd_ticket_approval_stage_position",
        ),
    )
    op.create_index(
        op.f("ix_service_desk_ticket_approval_stages_ticket_id"),
        "service_desk_ticket_approval_stages",
        ["ticket_id"],
    )
    op.create_table(
        "service_desk_ticket_approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_approval_stage_id", sa.Uuid(), nullable=False),
        sa.Column("approver_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("decision_comment", sa.String(length=2000), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approver_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(
            ["ticket_approval_stage_id"],
            ["service_desk_ticket_approval_stages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticket_approval_stage_id",
            "approver_user_id",
            name="uq_sd_ticket_approval_user",
        ),
    )
    op.create_index(
        op.f("ix_service_desk_ticket_approvals_approver_user_id"),
        "service_desk_ticket_approvals",
        ["approver_user_id"],
    )
    op.create_index(
        op.f("ix_service_desk_ticket_approvals_ticket_approval_stage_id"),
        "service_desk_ticket_approvals",
        ["ticket_approval_stage_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_ticket_approvals_ticket_approval_stage_id"),
        table_name="service_desk_ticket_approvals",
    )
    op.drop_index(
        op.f("ix_service_desk_ticket_approvals_approver_user_id"),
        table_name="service_desk_ticket_approvals",
    )
    op.drop_table("service_desk_ticket_approvals")
    op.drop_index(
        op.f("ix_service_desk_ticket_approval_stages_ticket_id"),
        table_name="service_desk_ticket_approval_stages",
    )
    op.drop_table("service_desk_ticket_approval_stages")
