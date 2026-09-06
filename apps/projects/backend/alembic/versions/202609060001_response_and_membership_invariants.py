"""enforce active response and project membership uniqueness

Revision ID: 202609060001
Revises: 202607060001
Create Date: 2026-09-06 00:01:00
"""

from collections.abc import Sequence

from alembic import op


revision: str = "202609060001"
down_revision: str | None = "202607060001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preserve legacy rows while making only the most recent active response authoritative.
    # Cancelled and soft-deleted rows deliberately stay outside the active-response invariant.
    op.execute(
        """
        WITH duplicates AS (
          SELECT id, row_number() OVER (
            PARTITION BY project_id, lower(email)
            ORDER BY created_at DESC, id DESC
          ) AS position
          FROM project_responses
          WHERE status <> 'cancelled' AND deleted_at IS NULL
        )
        UPDATE project_responses
        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
        WHERE id IN (SELECT id FROM duplicates WHERE position > 1)
        """
    )
    op.execute(
        """
        WITH duplicates AS (
          SELECT id, row_number() OVER (
            PARTITION BY project_id, user_id
            ORDER BY created_at DESC, id DESC
          ) AS position
          FROM project_responses
          WHERE user_id IS NOT NULL AND status <> 'cancelled' AND deleted_at IS NULL
        )
        UPDATE project_responses
        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
        WHERE id IN (SELECT id FROM duplicates WHERE position > 1)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_project_responses_active_project_email
        ON project_responses (project_id, lower(email))
        WHERE status <> 'cancelled' AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_project_responses_active_project_user
        ON project_responses (project_id, user_id)
        WHERE user_id IS NOT NULL AND status <> 'cancelled' AND deleted_at IS NULL
        """
    )
    # Existing application behavior treats one person as one member regardless of role.
    # Keep the earliest legacy membership and remove only redundant duplicates.
    op.execute(
        """
        DELETE FROM project_members
        WHERE id IN (
          SELECT id FROM (
            SELECT id, row_number() OVER (
              PARTITION BY project_id, user_id ORDER BY created_at ASC, id ASC
            ) AS position
            FROM project_members
          ) duplicates
          WHERE position > 1
        )
        """
    )
    op.create_unique_constraint(
        "uq_project_members_project_user", "project_members", ["project_id", "user_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_project_members_project_user", "project_members", type_="unique")
    op.execute("DROP INDEX uq_project_responses_active_project_user")
    op.execute("DROP INDEX uq_project_responses_active_project_email")
