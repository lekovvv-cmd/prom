"""add ticket attachments

Revision ID: 202607100013
Revises: 202607100012
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100013"
down_revision = "202607100012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["service_desk_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(op.f("ix_service_desk_attachments_owner_id"), "service_desk_attachments", ["owner_id"])
    op.create_index(op.f("ix_service_desk_attachments_owner_type"), "service_desk_attachments", ["owner_type"])
    op.create_index(op.f("ix_service_desk_attachments_ticket_id"), "service_desk_attachments", ["ticket_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_attachments_ticket_id"), table_name="service_desk_attachments")
    op.drop_index(op.f("ix_service_desk_attachments_owner_type"), table_name="service_desk_attachments")
    op.drop_index(op.f("ix_service_desk_attachments_owner_id"), table_name="service_desk_attachments")
    op.drop_table("service_desk_attachments")
