"""Expand Projects attachments to the platform file contract.

Revision ID: 202607160002
Revises: 202607160001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607160002"
down_revision: str | None = "202607160001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "attachments",
        sa.Column(
            "module",
            sa.String(length=64),
            nullable=False,
            server_default="projects",
        ),
    )
    op.add_column("attachments", sa.Column("storage_key", sa.String(length=1024)))
    op.add_column("attachments", sa.Column("original_name", sa.String(length=255)))
    op.add_column("attachments", sa.Column("safe_name", sa.String(length=255)))
    op.add_column(
        "attachments",
        sa.Column("content_type_declared", sa.String(length=255)),
    )
    op.add_column(
        "attachments",
        sa.Column("content_type_detected", sa.String(length=255)),
    )
    op.add_column("attachments", sa.Column("checksum", sa.String(length=64)))
    op.add_column(
        "attachments",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="available",
        ),
    )
    op.add_column(
        "attachments",
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        "UPDATE attachments SET original_name = file_name, safe_name = file_name, "
        "content_type_declared = content_type, content_type_detected = content_type"
    )
    op.create_index(
        op.f("ix_attachments_checksum"),
        "attachments",
        ["checksum"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attachments_status"),
        "attachments",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attachments_deleted_at"),
        "attachments",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attachments_storage_key"),
        "attachments",
        ["storage_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_attachments_storage_key"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_deleted_at"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_status"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_checksum"), table_name="attachments")
    op.drop_column("attachments", "deleted_at")
    op.drop_column("attachments", "status")
    op.drop_column("attachments", "checksum")
    op.drop_column("attachments", "content_type_detected")
    op.drop_column("attachments", "content_type_declared")
    op.drop_column("attachments", "safe_name")
    op.drop_column("attachments", "original_name")
    op.drop_column("attachments", "storage_key")
    op.drop_column("attachments", "module")
