"""service desk default assignment

Revision ID: 202607100010
Revises: 202607100009
Create Date: 2026-07-10 08:45:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607100010"
down_revision: str | None = "202607100009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("service_desk_services") as batch_op:
        batch_op.add_column(sa.Column("default_assignee_user_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_sd_service_default_assignee",
            "service_desk_users",
            ["default_assignee_user_id"],
            ["id"],
        )

    with op.batch_alter_table("service_desk_template_versions") as batch_op:
        batch_op.add_column(sa.Column("default_assignee_user_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_sd_template_version_default_assignee",
            "service_desk_users",
            ["default_assignee_user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("service_desk_template_versions") as batch_op:
        batch_op.drop_constraint("fk_sd_template_version_default_assignee", type_="foreignkey")
        batch_op.drop_column("default_assignee_user_id")

    with op.batch_alter_table("service_desk_services") as batch_op:
        batch_op.drop_constraint("fk_sd_service_default_assignee", type_="foreignkey")
        batch_op.drop_column("default_assignee_user_id")
