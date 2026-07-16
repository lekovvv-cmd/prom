"""service desk approval workflow configuration

Revision ID: 202607100008
Revises: 202607100007
Create Date: 2026-07-10 03:30:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607100008"
down_revision: str | None = "202607100007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_desk_template_versions",
        sa.Column("approval_mode", sa.String(length=32), server_default="none", nullable=False),
    )
    op.create_table(
        "service_desk_approval_workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_version_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_version_id"], ["service_desk_template_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_version_id"),
    )
    op.create_index(
        op.f("ix_service_desk_approval_workflows_template_version_id"),
        "service_desk_approval_workflows",
        ["template_version_id"],
    )
    op.create_table(
        "service_desk_approval_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("decision_rule", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["service_desk_approval_workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_approval_stages_workflow_id"),
        "service_desk_approval_stages",
        ["workflow_id"],
    )
    op.create_table(
        "service_desk_approval_stage_approvers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("service_desk_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["service_desk_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["service_desk_approval_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stage_id",
            "service_desk_user_id",
            name="uq_sd_stage_approver_user",
        ),
    )
    op.create_index(
        op.f("ix_service_desk_approval_stage_approvers_service_desk_user_id"),
        "service_desk_approval_stage_approvers",
        ["service_desk_user_id"],
    )
    op.create_index(
        op.f("ix_service_desk_approval_stage_approvers_stage_id"),
        "service_desk_approval_stage_approvers",
        ["stage_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_desk_approval_stage_approvers_stage_id"),
        table_name="service_desk_approval_stage_approvers",
    )
    op.drop_index(
        op.f("ix_service_desk_approval_stage_approvers_service_desk_user_id"),
        table_name="service_desk_approval_stage_approvers",
    )
    op.drop_table("service_desk_approval_stage_approvers")
    op.drop_index(
        op.f("ix_service_desk_approval_stages_workflow_id"),
        table_name="service_desk_approval_stages",
    )
    op.drop_table("service_desk_approval_stages")
    op.drop_index(
        op.f("ix_service_desk_approval_workflows_template_version_id"),
        table_name="service_desk_approval_workflows",
    )
    op.drop_table("service_desk_approval_workflows")
    op.drop_column("service_desk_template_versions", "approval_mode")
