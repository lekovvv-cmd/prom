"""add field key to ticket attachments

Revision ID: 202607100014
Revises: 202607100013
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "202607100014"
down_revision = "202607100013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("service_desk_attachments", sa.Column("field_key", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_service_desk_attachments_field_key"), "service_desk_attachments", ["field_key"])


def downgrade() -> None:
    op.drop_index(op.f("ix_service_desk_attachments_field_key"), table_name="service_desk_attachments")
    op.drop_column("service_desk_attachments", "field_key")
