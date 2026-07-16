"""add attachments

Revision ID: 202607020002
Revises: 202607020001
Create Date: 2026-07-02 18:10:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020002"
down_revision: str | None = "202607020001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_attachments_owner_id"), "attachments", ["owner_id"], unique=False)
    op.create_index(op.f("ix_attachments_owner_type"), "attachments", ["owner_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_attachments_owner_type"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_owner_id"), table_name="attachments")
    op.drop_table("attachments")
