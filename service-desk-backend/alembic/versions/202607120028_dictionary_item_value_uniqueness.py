"""Enforce normalized dictionary item value uniqueness.

Revision ID: 202607120028
Revises: 202607120027
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607120028"
down_revision: str | None = "202607120027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM service_desk_dictionary_items
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           row_number() OVER (
                               PARTITION BY dictionary_id, lower(trim(value))
                               ORDER BY created_at, id
                           ) AS duplicate_number
                    FROM service_desk_dictionary_items
                ) AS ranked
                WHERE duplicate_number > 1
            )
            """
        )
    )
    op.create_index(
        "uq_service_desk_dictionary_items_dictionary_value_normalized",
        "service_desk_dictionary_items",
        ["dictionary_id", sa.text("lower(trim(value))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_service_desk_dictionary_items_dictionary_value_normalized",
        table_name="service_desk_dictionary_items",
    )
