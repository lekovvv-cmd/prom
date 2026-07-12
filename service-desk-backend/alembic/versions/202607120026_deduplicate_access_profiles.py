"""Merge duplicate access profiles and make normalized email unique.

Revision ID: 202607120026
Revises: 202607120025
"""

from collections import defaultdict
from collections.abc import Sequence
import json

from alembic import op
import sqlalchemy as sa

revision: str = "202607120026"
down_revision: str | None = "202607120025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


REFERENCE_COLUMNS = (
    ("service_desk_user_capabilities", "service_desk_user_id"),
    ("service_desk_access_audit_events", "actor_user_id"),
    ("service_desk_access_audit_events", "target_user_id"),
    ("service_desk_services", "default_assignee_user_id"),
    ("service_desk_template_versions", "default_assignee_user_id"),
    ("service_desk_tickets", "requester_user_id"),
    ("service_desk_tickets", "assignee_user_id"),
    ("service_desk_ticket_history", "actor_user_id"),
    ("service_desk_comments", "author_user_id"),
    ("service_desk_attachments", "uploaded_by_user_id"),
    ("service_desk_escalation_rules", "recipient_user_id"),
    ("service_desk_sla_escalation_events", "recipient_user_id"),
)


def _merge_unique_rows(connection, table, user_column, key_column, duplicate, canonical):
    rows = connection.execute(
        sa.text(f"SELECT id, {key_column} FROM {table} WHERE {user_column} = :user_id"),
        {"user_id": duplicate},
    ).all()
    canonical_keys = {
        row[0]
        for row in connection.execute(
            sa.text(f"SELECT {key_column} FROM {table} WHERE {user_column} = :user_id"),
            {"user_id": canonical},
        ).all()
    }
    for row_id, key in rows:
        if key in canonical_keys:
            connection.execute(
                sa.text(f"DELETE FROM {table} WHERE id = :row_id"), {"row_id": row_id}
            )
        else:
            connection.execute(
                sa.text(f"UPDATE {table} SET {user_column} = :canonical WHERE id = :row_id"),
                {"canonical": canonical, "row_id": row_id},
            )


def _replace_routing_references(connection, duplicate, canonical):
    for row_id, action in connection.execute(
        sa.text("SELECT id, action FROM service_desk_routing_rules")
    ).all():
        parsed = json.loads(action) if isinstance(action, str) else action
        if not isinstance(parsed, dict) or str(parsed.get("user_id")) != str(duplicate):
            continue
        parsed["user_id"] = str(canonical)
        connection.execute(
            sa.text("UPDATE service_desk_routing_rules SET action = :action WHERE id = :row_id"),
            {"action": json.dumps(parsed), "row_id": row_id},
        )


def upgrade() -> None:
    connection = op.get_bind()
    profiles = connection.execute(
        sa.text(
            "SELECT id, email, identity_user_id, access_type, is_active, created_at "
            "FROM service_desk_users"
        )
    ).mappings()
    grouped = defaultdict(list)
    for profile in profiles:
        grouped[str(profile["email"] or "").strip().lower()].append(profile)

    for normalized_email, duplicates in grouped.items():
        if not normalized_email:
            continue
        ordered = sorted(
            duplicates,
            key=lambda item: (
                not bool(item["is_active"]),
                item["access_type"] != "service_desk_admin",
                item["created_at"],
                str(item["id"]),
            ),
        )
        canonical = ordered[0]
        connection.execute(
            sa.text("UPDATE service_desk_users SET email = :email WHERE id = :user_id"),
            {"email": normalized_email, "user_id": canonical["id"]},
        )
        for duplicate in ordered[1:]:
            duplicate_id = duplicate["id"]
            canonical_id = canonical["id"]
            _merge_unique_rows(
                connection,
                "service_desk_approval_stage_approvers",
                "service_desk_user_id",
                "stage_id",
                duplicate_id,
                canonical_id,
            )
            _merge_unique_rows(
                connection,
                "service_desk_ticket_approvals",
                "approver_user_id",
                "ticket_approval_stage_id",
                duplicate_id,
                canonical_id,
            )
            _merge_unique_rows(
                connection,
                "service_desk_notifications",
                "recipient_user_id",
                "event_id",
                duplicate_id,
                canonical_id,
            )
            for table, column in REFERENCE_COLUMNS:
                connection.execute(
                    sa.text(f"UPDATE {table} SET {column} = :canonical WHERE {column} = :duplicate"),
                    {"canonical": canonical_id, "duplicate": duplicate_id},
                )
            _replace_routing_references(connection, duplicate_id, canonical_id)
            connection.execute(
                sa.text("DELETE FROM service_desk_users WHERE id = :user_id"),
                {"user_id": duplicate_id},
            )

    with op.batch_alter_table("service_desk_users") as batch_op:
        batch_op.create_unique_constraint("uq_service_desk_users_email", ["email"])


def downgrade() -> None:
    with op.batch_alter_table("service_desk_users") as batch_op:
        batch_op.drop_constraint("uq_service_desk_users_email", type_="unique")
