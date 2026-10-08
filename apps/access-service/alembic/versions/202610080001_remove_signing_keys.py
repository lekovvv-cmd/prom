"""Remove the unused database signing key ring.

Revision ID: 202610080001
Revises: 202610070001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202610080001"
down_revision: str | None = "202610070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_signing_keys_status", table_name="signing_keys")
    op.drop_index("ix_signing_keys_kid", table_name="signing_keys")
    op.drop_table("signing_keys")


def downgrade() -> None:
    op.create_table(
        "signing_keys",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kid", sa.String(length=128), nullable=False),
        sa.Column("private_key_pem", sa.Text()),
        sa.Column("public_key_pem", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("retired_at", sa.DateTime(timezone=True)),
        sa.Column("verify_until", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_signing_keys_kid", "signing_keys", ["kid"], unique=True)
    op.create_index("ix_signing_keys_status", "signing_keys", ["status"])
