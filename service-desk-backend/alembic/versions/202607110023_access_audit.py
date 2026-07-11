"""access administration audit

Revision ID: 202607110023
Revises: 202607110022
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "202607110023"
down_revision: str | None = "202607110022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_desk_access_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["service_desk_users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["service_desk_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_service_desk_access_audit_events_actor_user_id",
        "service_desk_access_audit_events",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_service_desk_access_audit_events_target_user_id",
        "service_desk_access_audit_events",
        ["target_user_id"],
    )
    op.create_index(
        "ix_service_desk_access_audit_events_event_type",
        "service_desk_access_audit_events",
        ["event_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_service_desk_access_audit_events_event_type",
        table_name="service_desk_access_audit_events",
    )
    op.drop_index(
        "ix_service_desk_access_audit_events_target_user_id",
        table_name="service_desk_access_audit_events",
    )
    op.drop_index(
        "ix_service_desk_access_audit_events_actor_user_id",
        table_name="service_desk_access_audit_events",
    )
    op.drop_table("service_desk_access_audit_events")
