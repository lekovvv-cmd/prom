"""Remove unused external OIDC login transactions.

Revision ID: 202610070001
Revises: 202609010001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202610070001"
down_revision: str | None = "202609010001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("oidc_login_transactions")


def downgrade() -> None:
    op.create_table(
        "oidc_login_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("pkce_verifier", sa.String(length=128), nullable=False),
        sa.Column("return_url", sa.String(length=2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_oidc_login_transactions_state_hash", "oidc_login_transactions", ["state_hash"], unique=True)
    op.create_index("ix_oidc_login_transactions_expires_at", "oidc_login_transactions", ["expires_at"])
    op.create_index("ix_oidc_login_transactions_consumed_at", "oidc_login_transactions", ["consumed_at"])
    op.create_index("ix_oidc_login_transactions_cleanup", "oidc_login_transactions", ["expires_at", "consumed_at"])
