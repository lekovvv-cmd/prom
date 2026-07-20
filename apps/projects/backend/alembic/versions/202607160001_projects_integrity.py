"""Add Projects audit, outbox, idempotency and optimistic versioning.

Revision ID: 202607160001
Revises: 202607120003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607160001"
down_revision: str | None = "202607120003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "project_outbox_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("aggregate_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=128), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    for column in (
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "status",
        "next_attempt_at",
        "created_at",
    ):
        op.create_index(
            op.f(f"ix_project_outbox_events_{column}"),
            "project_outbox_events",
            [column],
            unique=False,
        )

    op.create_table(
        "project_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=64), nullable=True),
        sa.Column("external_user_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("object_type", sa.String(length=128), nullable=False),
        sa.Column("object_id", sa.String(length=255), nullable=False),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "actor_user_id",
        "external_user_id",
        "action",
        "module",
        "object_type",
        "object_id",
        "request_id",
        "created_at",
    ):
        op.create_index(
            op.f(f"ix_project_audit_events_{column}"),
            "project_audit_events",
            [column],
            unique=False,
        )

    op.create_table(
        "project_idempotency_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scope", sa.String(length=160), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scope",
            "idempotency_key",
            name="uq_project_idempotency_scope_key",
        ),
    )
    op.create_index(
        op.f("ix_project_idempotency_records_scope"),
        "project_idempotency_records",
        ["scope"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_idempotency_records_expires_at"),
        "project_idempotency_records",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_project_idempotency_records_expires_at"),
        table_name="project_idempotency_records",
    )
    op.drop_index(
        op.f("ix_project_idempotency_records_scope"),
        table_name="project_idempotency_records",
    )
    op.drop_table("project_idempotency_records")

    for column in (
        "created_at",
        "request_id",
        "object_id",
        "object_type",
        "module",
        "action",
        "external_user_id",
        "actor_user_id",
    ):
        op.drop_index(
            op.f(f"ix_project_audit_events_{column}"),
            table_name="project_audit_events",
        )
    op.drop_table("project_audit_events")

    for column in (
        "created_at",
        "next_attempt_at",
        "status",
        "aggregate_id",
        "aggregate_type",
        "event_type",
    ):
        op.drop_index(
            op.f(f"ix_project_outbox_events_{column}"),
            table_name="project_outbox_events",
        )
    op.drop_table("project_outbox_events")
    op.drop_column("projects", "version")
