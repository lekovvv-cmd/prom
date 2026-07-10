"""add Service Desk notifications

Revision ID: 202607110021
Revises: 202607110020
"""
from alembic import op
import sqlalchemy as sa

revision = "202607110021"
down_revision = "202607110020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.String(length=1000), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "recipient_user_id", name="uq_sd_notification_event_recipient"),
    )
    for columns, name in [(["event_id"], "ix_service_desk_notifications_event_id"), (["recipient_user_id"], "ix_service_desk_notifications_recipient_user_id"), (["ticket_id"], "ix_service_desk_notifications_ticket_id"), (["event_type"], "ix_service_desk_notifications_event_type"), (["is_read"], "ix_service_desk_notifications_is_read")]:
        op.create_index(name, "service_desk_notifications", columns)


def downgrade() -> None:
    op.drop_table("service_desk_notifications")
