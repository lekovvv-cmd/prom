"""Store pilot attachment bytes in the Projects database."""

import sqlalchemy as sa
from alembic import op

revision = "202610210001"
down_revision = "202609060004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachment_blobs",
        sa.Column("key", sa.String(length=1024), primary_key=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("attachment_blobs")
