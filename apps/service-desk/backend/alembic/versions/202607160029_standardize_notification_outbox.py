"""Standardize the Service Desk notification outbox contract.

Revision ID: 202607160029
Revises: 202607120028
"""

from collections.abc import Sequence
import json

import sqlalchemy as sa
from alembic import op

revision: str = "202607160029"
down_revision: str | None = "202607120028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column(
            "event_type",
            sa.String(length=160),
            nullable=False,
            server_default="NotificationDeliveryRequested",
        ),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column(
            "aggregate_type",
            sa.String(length=128),
            nullable=False,
            server_default="service_desk_ticket",
        ),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("aggregate_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("payload_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("locked_by", sa.String(length=128), nullable=True),
    )

    outbox = sa.table(
        "service_desk_notification_outbox",
        sa.column("id", sa.Uuid()),
        sa.column("event_id", sa.Uuid()),
        sa.column("payload", sa.JSON()),
        sa.column("status", sa.String()),
        sa.column("retry_count", sa.Integer()),
        sa.column("next_retry_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("event_type", sa.String()),
        sa.column("aggregate_id", sa.String()),
        sa.column("attempts", sa.Integer()),
        sa.column("next_attempt_at", sa.DateTime(timezone=True)),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(outbox)).mappings().all()
    for row in rows:
        payload = row["payload"] or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        status = {
            "sent": "processed",
            "failed": "retry",
        }.get(row["status"], row["status"])
        connection.execute(
            sa.update(outbox)
            .where(outbox.c.id == row["id"])
            .values(
                event_type=str(
                    payload.get("event_type") or "NotificationDeliveryRequested"
                ),
                aggregate_id=str(payload.get("ticket_id") or row["event_id"]),
                attempts=row["retry_count"],
                next_attempt_at=row["next_retry_at"] or row["created_at"],
                status=status,
            )
        )
    op.alter_column(
        "service_desk_notification_outbox",
        "aggregate_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "service_desk_notification_outbox",
        "next_attempt_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "service_desk_notification_outbox",
        "last_error",
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.drop_column("service_desk_notification_outbox", "next_retry_at")
    op.drop_column("service_desk_notification_outbox", "retry_count")

    for column in (
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "next_attempt_at",
        "created_at",
    ):
        op.create_index(
            op.f(f"ix_service_desk_notification_outbox_{column}"),
            "service_desk_notification_outbox",
            [column],
            unique=False,
        )

    for column in ("event_type", "aggregate_type", "payload_version", "attempts"):
        op.alter_column(
            "service_desk_notification_outbox",
            column,
            server_default=None,
        )


def downgrade() -> None:
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "service_desk_notification_outbox",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE service_desk_notification_outbox
            SET retry_count = attempts,
                next_retry_at = next_attempt_at,
                status = CASE
                    WHEN status = 'processed' THEN 'sent'
                    WHEN status = 'retry' THEN 'failed'
                    ELSE status
                END
            """
        )
    )
    op.alter_column(
        "service_desk_notification_outbox",
        "last_error",
        existing_type=sa.Text(),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )
    for column in (
        "created_at",
        "next_attempt_at",
        "aggregate_id",
        "aggregate_type",
        "event_type",
    ):
        op.drop_index(
            op.f(f"ix_service_desk_notification_outbox_{column}"),
            table_name="service_desk_notification_outbox",
        )
    for column in (
        "locked_by",
        "locked_at",
        "next_attempt_at",
        "attempts",
        "payload_version",
        "aggregate_id",
        "aggregate_type",
        "event_type",
    ):
        op.drop_column("service_desk_notification_outbox", column)
