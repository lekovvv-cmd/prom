"""add project stages and tasks

Revision ID: 202607060001
Revises: 202607050003
Create Date: 2026-07-06 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607060001"
down_revision: str | None = "202607050003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_stages_project_id"), "project_stages", ["project_id"], unique=False)

    op.create_table(
        "project_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["project_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_tasks_assignee_user_id"), "project_tasks", ["assignee_user_id"], unique=False)
    op.create_index(op.f("ix_project_tasks_due_date"), "project_tasks", ["due_date"], unique=False)
    op.create_index(op.f("ix_project_tasks_project_id"), "project_tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_tasks_stage_id"), "project_tasks", ["stage_id"], unique=False)
    op.create_index(op.f("ix_project_tasks_status"), "project_tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_tasks_status"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_stage_id"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_project_id"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_due_date"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_assignee_user_id"), table_name="project_tasks")
    op.drop_table("project_tasks")
    op.drop_index(op.f("ix_project_stages_project_id"), table_name="project_stages")
    op.drop_table("project_stages")
