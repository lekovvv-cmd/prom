"""merge projects integrity and concurrency migration heads

Revision ID: 202609060004
Revises: 202607160002, 202609060003
Create Date: 2026-09-06 00:04:00
"""

from collections.abc import Sequence


revision: str = "202609060004"
down_revision: tuple[str, str] = ("202607160002", "202609060003")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
