"""Add persisted signing key ring and browser sessions.

Revision ID: 202607220001
Revises: 202607160001
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607220001"
down_revision: str | None = "202607160001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "signing_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kid", sa.String(length=128), nullable=False),
        sa.Column("private_key_pem", sa.Text()),
        sa.Column("public_key_pem", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("retired_at", sa.DateTime(timezone=True)),
        sa.Column("verify_until", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signing_keys_kid", "signing_keys", ["kid"], unique=True)
    op.create_index("ix_signing_keys_status", "signing_keys", ["status"])
    op.create_table(
        "browser_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("session_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["platform_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_browser_sessions_token_hash", "browser_sessions", ["token_hash"], unique=True)
    op.create_index("ix_browser_sessions_user_id", "browser_sessions", ["user_id"])
    op.create_index("ix_browser_sessions_idle_expires_at", "browser_sessions", ["idle_expires_at"])
    op.create_index("ix_browser_sessions_absolute_expires_at", "browser_sessions", ["absolute_expires_at"])
    op.create_index("ix_browser_sessions_revoked_at", "browser_sessions", ["revoked_at"])


def downgrade() -> None:
    op.drop_index("ix_browser_sessions_revoked_at", table_name="browser_sessions")
    op.drop_index("ix_browser_sessions_absolute_expires_at", table_name="browser_sessions")
    op.drop_index("ix_browser_sessions_idle_expires_at", table_name="browser_sessions")
    op.drop_index("ix_browser_sessions_user_id", table_name="browser_sessions")
    op.drop_index("ix_browser_sessions_token_hash", table_name="browser_sessions")
    op.drop_table("browser_sessions")
    op.drop_index("ix_signing_keys_status", table_name="signing_keys")
    op.drop_index("ix_signing_keys_kid", table_name="signing_keys")
    op.drop_table("signing_keys")
