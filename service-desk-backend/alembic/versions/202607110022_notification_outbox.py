"""add Service Desk notification outbox

Revision ID: 202607110022
Revises: 202607110021
"""
from alembic import op
import sqlalchemy as sa

revision = "202607110022"
down_revision = "202607110021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_notification_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "channel", "recipient", name="uq_sd_outbox_event_channel_recipient"),
    )
    for column in ("event_id", "channel", "recipient", "status"):
        op.create_index(f"ix_service_desk_notification_outbox_{column}", "service_desk_notification_outbox", [column])


def downgrade() -> None:
    op.drop_table("service_desk_notification_outbox")
