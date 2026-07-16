"""add ticket comments

Revision ID: 202607100012
Revises: 202607100011
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100012"
down_revision = "202607100011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_desk_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_desk_tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_desk_comments_ticket_id"),
        "service_desk_comments",
        ["ticket_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_comments_ticket_id"), table_name="service_desk_comments")
    op.drop_table("service_desk_comments")
