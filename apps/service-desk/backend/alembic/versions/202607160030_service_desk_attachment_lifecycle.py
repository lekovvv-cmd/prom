"""Expand Service Desk attachments to the platform file lifecycle.

Revision ID: 202607160030
Revises: 202607160029
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607160030"
down_revision: str | None = "202607160029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_desk_attachments",
        sa.Column(
            "module",
            sa.String(length=64),
            nullable=False,
            server_default="service-desk",
        ),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("original_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("safe_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("content_type_declared", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("content_type_detected", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("checksum", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="available",
        ),
    )
    op.add_column(
        "service_desk_attachments",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE service_desk_attachments
        SET original_name = file_name,
            safe_name = file_name,
            content_type_declared = content_type,
            content_type_detected = content_type
        """
    )
    op.alter_column(
        "service_desk_attachments",
        "original_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "service_desk_attachments",
        "safe_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    for column in ("checksum", "status", "deleted_at"):
        op.create_index(
            op.f(f"ix_service_desk_attachments_{column}"),
            "service_desk_attachments",
            [column],
            unique=False,
        )
    op.alter_column(
        "service_desk_attachments",
        "module",
        server_default=None,
    )
    op.alter_column(
        "service_desk_attachments",
        "status",
        server_default=None,
    )


def downgrade() -> None:
    for column in ("deleted_at", "status", "checksum"):
        op.drop_index(
            op.f(f"ix_service_desk_attachments_{column}"),
            table_name="service_desk_attachments",
        )
    for column in (
        "deleted_at",
        "status",
        "checksum",
        "content_type_detected",
        "content_type_declared",
        "safe_name",
        "original_name",
        "module",
    ):
        op.drop_column("service_desk_attachments", column)
