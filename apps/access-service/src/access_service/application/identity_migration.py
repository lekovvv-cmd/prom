from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, MetaData, Table, Uuid, create_engine, select, update
from sqlalchemy.orm import Session

from access_service.application.catalog import ensure_access_catalog
from access_service.domain.models import (
    AccessAuditEvent,
    GroupMembership,
    PlatformUser,
    UserRoleAssignment,
)


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PROJECT_ROLE_MAP = {
    "admin": "platform_admin",
    "platform_admin": "platform_admin",
    "project_manager": "project_manager",
    "employee": "employee",
}
SERVICE_DESK_ROLE_MAP = {
    "service_desk_manager": "service_desk_manager",
    "service_desk_admin": "service_desk_admin",
}


class IdentityMigrationConflict(RuntimeError):
    pass


@dataclass
class IdentityRecord:
    user_id: str
    email: str
    display_name: str
    department: str | None = None
    position: str | None = None
    is_active: bool = True
    external_subject: str | None = None
    role_codes: set[str] = field(default_factory=set)
    project_user_ids: list[str] = field(default_factory=list)
    service_desk_user_ids: list[str] = field(default_factory=list)
    current_access_user_id: str | None = None
    action: str = "create"

    def report_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["role_codes"] = sorted(self.role_codes)
        return result


@dataclass
class ReconciliationPlan:
    records: list[IdentityRecord]
    conflicts: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def can_apply(self) -> bool:
        return not self.conflicts

    def report_dict(self, *, mode: str, applied: bool) -> dict[str, Any]:
        action_counts: dict[str, int] = {}
        for record in self.records:
            action_counts[record.action] = action_counts.get(record.action, 0) + 1
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "applied": applied,
            "can_apply": self.can_apply,
            "summary": {
                "identities": len(self.records),
                "conflicts": len(self.conflicts),
                "warnings": len(self.warnings),
                "actions": action_counts,
            },
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "identities": [record.report_dict() for record in self.records],
        }


def normalize_email(value: object) -> str:
    email = str(value or "").strip().casefold()
    if len(email) > 320 or EMAIL_PATTERN.fullmatch(email) is None:
        raise ValueError(f"Invalid email: {value!r}")
    return email


def _string_value(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _enum_value(value: object | None) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").strip()


def _load_table(engine: Engine, table_name: str) -> Table:
    return Table(table_name, MetaData(), autoload_with=engine)


def _rows(engine: Engine, table_name: str) -> tuple[Table, list[dict[str, Any]]]:
    table = _load_table(engine, table_name)
    with engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(select(table)).mappings()]
    return table, rows


def _source_email(
    row: dict[str, Any],
    *,
    source: str,
    conflicts: list[dict[str, str]],
) -> str | None:
    try:
        return normalize_email(row.get("email"))
    except ValueError as exc:
        conflicts.append(
            {
                "type": "invalid_email",
                "source": source,
                "record_id": str(row.get("id", "")),
                "detail": str(exc),
            }
        )
        return None


def _detect_source_duplicates(
    rows: list[dict[str, Any]],
    *,
    source: str,
    conflicts: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    by_email: dict[str, dict[str, Any]] = {}
    for row in rows:
        email = _source_email(row, source=source, conflicts=conflicts)
        if email is None:
            continue
        previous = by_email.get(email)
        if previous is not None:
            conflicts.append(
                {
                    "type": "duplicate_email",
                    "source": source,
                    "record_id": str(row.get("id", "")),
                    "detail": (
                        f"{email} belongs to both {previous.get('id')} and {row.get('id')}"
                    ),
                }
            )
            continue
        by_email[email] = row
    return by_email


def build_reconciliation_plan(
    *,
    projects_engine: Engine,
    service_desk_engine: Engine,
    access_engine: Engine,
) -> ReconciliationPlan:
    _, project_rows = _rows(projects_engine, "users")
    _, service_desk_rows = _rows(service_desk_engine, "service_desk_users")
    _, access_rows = _rows(access_engine, "platform_users")

    plan = ReconciliationPlan(records=[])
    projects_by_email = _detect_source_duplicates(
        project_rows,
        source="projects",
        conflicts=plan.conflicts,
    )
    service_desk_by_email = _detect_source_duplicates(
        service_desk_rows,
        source="service-desk",
        conflicts=plan.conflicts,
    )
    access_by_email = _detect_source_duplicates(
        access_rows,
        source="access",
        conflicts=plan.conflicts,
    )
    access_by_id = {str(row["id"]): row for row in access_rows}
    access_by_subject: dict[str, dict[str, Any]] = {}
    for row in access_rows:
        subject = _string_value(row.get("external_subject"))
        if subject is None:
            continue
        if subject in access_by_subject:
            plan.conflicts.append(
                {
                    "type": "external_subject_conflict",
                    "source": "access",
                    "record_id": str(row["id"]),
                    "detail": f"External subject {subject!r} is assigned more than once",
                }
            )
        access_by_subject[subject] = row

    records_by_email: dict[str, IdentityRecord] = {}
    project_ids_to_email: dict[str, str] = {}
    for email, row in projects_by_email.items():
        user_id = str(row["id"])
        existing_email = project_ids_to_email.get(user_id)
        if existing_email is not None and existing_email != email:
            plan.conflicts.append(
                {
                    "type": "uuid_conflict",
                    "source": "projects",
                    "record_id": user_id,
                    "detail": f"Projects UUID maps to both {existing_email} and {email}",
                }
            )
        project_ids_to_email[user_id] = email
        role = PROJECT_ROLE_MAP.get(_enum_value(row.get("role")))
        if role is None:
            plan.conflicts.append(
                {
                    "type": "unknown_role",
                    "source": "projects",
                    "record_id": user_id,
                    "detail": f"Unknown Projects role {row.get('role')!r}",
                }
            )
        record = IdentityRecord(
            user_id=user_id,
            email=email,
            display_name=str(row.get("full_name") or email),
            department=_string_value(row.get("department")),
            position=_string_value(row.get("position")),
            external_subject=_string_value(row.get("external_subject")),
            project_user_ids=[user_id],
        )
        if role is not None:
            record.role_codes.add(role)
        records_by_email[email] = record

    for email, row in service_desk_by_email.items():
        projection_id = str(row["id"])
        source_identity_id = _string_value(row.get("identity_user_id"))
        service_record = records_by_email.get(email)
        if source_identity_id in project_ids_to_email:
            owner_email = project_ids_to_email[source_identity_id]
            if owner_email != email:
                plan.conflicts.append(
                    {
                        "type": "uuid_conflict",
                        "source": "service-desk",
                        "record_id": projection_id,
                        "detail": (
                            f"Projection identity {source_identity_id} belongs to {owner_email}, not {email}"
                        ),
                    }
                )
        if service_record is None:
            candidate_id = source_identity_id or projection_id
            try:
                uuid.UUID(candidate_id)
            except (ValueError, AttributeError):
                candidate_id = projection_id
            service_record = IdentityRecord(
                user_id=candidate_id,
                email=email,
                display_name=str(row.get("display_name") or email),
                department=_string_value(row.get("department")),
                position=_string_value(row.get("position")),
                external_subject=_string_value(row.get("external_subject")),
            )
            records_by_email[email] = service_record
        elif service_record.external_subject is None:
            service_record.external_subject = _string_value(row.get("external_subject"))
        service_record.service_desk_user_ids.append(projection_id)
        service_record.is_active = service_record.is_active and bool(
            row.get("is_active", True)
        )
        role = SERVICE_DESK_ROLE_MAP.get(_enum_value(row.get("access_type")))
        if role is None:
            plan.conflicts.append(
                {
                    "type": "unknown_role",
                    "source": "service-desk",
                    "record_id": projection_id,
                    "detail": f"Unknown Service Desk access type {row.get('access_type')!r}",
                }
            )
        else:
            service_record.role_codes.add(role)

    for email, record in records_by_email.items():
        existing_by_email = access_by_email.get(email)
        existing_by_id = access_by_id.get(record.user_id)
        existing_by_subject = (
            access_by_subject.get(record.external_subject) if record.external_subject else None
        )
        candidates = {
            str(candidate["id"])
            for candidate in (existing_by_email, existing_by_id, existing_by_subject)
            if candidate is not None
        }
        if len(candidates) > 1:
            plan.conflicts.append(
                {
                    "type": "uuid_conflict",
                    "source": "access",
                    "record_id": record.user_id,
                    "detail": (
                        f"Identity {email} resolves to multiple Access users: {sorted(candidates)}"
                    ),
                }
            )
            continue
        existing = existing_by_subject or existing_by_id or existing_by_email
        if existing is not None:
            record.current_access_user_id = str(existing["id"])
            existing_subject = _string_value(existing.get("external_subject"))
            if record.external_subject and existing_subject not in {None, record.external_subject}:
                plan.conflicts.append(
                    {
                        "type": "external_subject_conflict",
                        "source": "access",
                        "record_id": str(existing["id"]),
                        "detail": (
                            f"Access user has {existing_subject!r}; source has {record.external_subject!r}"
                        ),
                    }
                )
            record.external_subject = record.external_subject or existing_subject
            record.is_active = record.is_active and bool(existing.get("is_active", True))
            if record.current_access_user_id != record.user_id:
                record.action = "rekey"
            else:
                comparable = {
                    "email": email,
                    "display_name": record.display_name,
                    "department": record.department,
                    "position": record.position,
                    "is_active": record.is_active,
                    "external_subject": record.external_subject,
                }
                record.action = (
                    "noop"
                    if all(existing.get(key) == value for key, value in comparable.items())
                    else "update"
                )
        plan.records.append(record)

    plan.records.sort(key=lambda item: item.email)
    return plan


def _rekey_access_user(session: Session, old_user: PlatformUser, record: IdentityRecord) -> PlatformUser:
    old_id = old_user.id
    old_subject = old_user.external_subject
    old_email = old_user.email
    old_user.external_subject = None
    old_user.email = f"migration-{uuid.uuid4()}@invalid.local"
    session.flush()
    user = PlatformUser(
        id=record.user_id,
        external_subject=record.external_subject or old_subject,
        email=record.email,
        display_name=record.display_name,
        department=record.department,
        position=record.position,
        is_active=record.is_active,
        session_version=old_user.session_version + 1,
        last_login_at=old_user.last_login_at,
        created_at=old_user.created_at,
    )
    session.add(user)
    session.flush()
    session.execute(
        update(UserRoleAssignment)
        .where(UserRoleAssignment.user_id == old_id)
        .values(user_id=record.user_id)
    )
    session.execute(
        update(UserRoleAssignment)
        .where(UserRoleAssignment.assigned_by_user_id == old_id)
        .values(assigned_by_user_id=record.user_id)
    )
    session.execute(
        update(GroupMembership)
        .where(GroupMembership.user_id == old_id)
        .values(user_id=record.user_id)
    )
    session.execute(
        update(AccessAuditEvent)
        .where(AccessAuditEvent.actor_user_id == old_id)
        .values(actor_user_id=record.user_id)
    )
    session.delete(old_user)
    session.flush()
    session.add(
        AccessAuditEvent(
            actor_user_id=None,
            action="legacy_identity_rekeyed",
            object_type="platform_user",
            object_id=record.user_id,
            before={"id": old_id, "email": old_email},
            after={"id": record.user_id, "email": record.email},
            source="identity-migration",
        )
    )
    return user


def _apply_access(plan: ReconciliationPlan, access_engine: Engine) -> None:
    with Session(access_engine, expire_on_commit=False) as session:
        roles = ensure_access_catalog(session)
        for record in plan.records:
            user = session.get(PlatformUser, record.user_id)
            if user is None and record.current_access_user_id:
                old_user = session.get(PlatformUser, record.current_access_user_id)
                if old_user is None:
                    raise IdentityMigrationConflict(
                        f"Access user {record.current_access_user_id} disappeared during apply"
                    )
                user = _rekey_access_user(session, old_user, record)
            elif user is None:
                user = PlatformUser(
                    id=record.user_id,
                    external_subject=record.external_subject,
                    email=record.email,
                    display_name=record.display_name,
                    department=record.department,
                    position=record.position,
                    is_active=record.is_active,
                )
                session.add(user)
                session.flush()

            before = {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "external_subject": user.external_subject,
            }
            changed = record.action in {"create", "rekey"}
            for attribute, value in (
                ("email", record.email),
                ("display_name", record.display_name),
                ("department", record.department),
                ("position", record.position),
                ("is_active", record.is_active),
                ("external_subject", record.external_subject),
            ):
                if getattr(user, attribute) != value:
                    setattr(user, attribute, value)
                    changed = True
            session.flush()
            assigned_role_ids = set(
                session.scalars(
                    select(UserRoleAssignment.role_id).where(
                        UserRoleAssignment.user_id == user.id
                    )
                ).all()
            )
            for role_code in sorted(record.role_codes):
                role = roles[role_code]
                if role.id not in assigned_role_ids:
                    session.add(UserRoleAssignment(user_id=user.id, role_id=role.id))
                    assigned_role_ids.add(role.id)
                    changed = True
            if changed and record.action not in {"create", "rekey"}:
                user.session_version += 1
            if changed:
                session.add(
                    AccessAuditEvent(
                        actor_user_id=None,
                        action="legacy_identity_migrated",
                        object_type="platform_user",
                        object_id=user.id,
                        before=before,
                        after={
                            "id": user.id,
                            "email": user.email,
                            "is_active": user.is_active,
                            "external_subject": user.external_subject,
                            "role_codes": sorted(record.role_codes),
                        },
                        source="identity-migration",
                    )
                )
        session.commit()


def _apply_service_desk(plan: ReconciliationPlan, service_desk_engine: Engine) -> None:
    table = _load_table(service_desk_engine, "service_desk_users")
    with service_desk_engine.begin() as connection:
        for record in plan.records:
            for projection_id in record.service_desk_user_ids:
                projection_key: str | uuid.UUID = projection_id
                if isinstance(table.c.id.type, Uuid):
                    projection_key = uuid.UUID(projection_id)
                connection.execute(
                    update(table)
                    .where(table.c.id == projection_key)
                    .values(identity_user_id=record.user_id, email=record.email)
                )


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Legacy identity reconciliation",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Mode: `{report['mode']}`",
        f"- Applied: `{report['applied']}`",
        f"- Can apply: `{report['can_apply']}`",
        f"- Identities: {summary['identities']}",
        f"- Conflicts: {summary['conflicts']}",
        "",
        "## Identities",
        "",
        "| Email | Platform UUID | Action | Roles | Projects | Service Desk |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["identities"]:
        lines.append(
            "| {email} | `{user_id}` | {action} | {roles} | {projects} | {service_desk} |".format(
                email=item["email"],
                user_id=item["user_id"],
                action=item["action"],
                roles=", ".join(item["role_codes"]),
                projects=", ".join(item["project_user_ids"]),
                service_desk=", ".join(item["service_desk_user_ids"]),
            )
        )
    lines.extend(["", "## Conflicts", ""])
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            lines.append(
                f"- **{conflict['type']}** ({conflict['source']} / {conflict['record_id']}): "
                f"{conflict['detail']}"
            )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def write_reconciliation_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "identity-reconciliation.json"
    markdown_path = report_dir / "identity-reconciliation.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def migrate_identities(
    *,
    projects_database_url: str,
    service_desk_database_url: str,
    access_database_url: str,
    apply: bool,
    report_dir: Path,
) -> dict[str, Any]:
    projects_engine = create_engine(projects_database_url)
    service_desk_engine = create_engine(service_desk_database_url)
    access_engine = create_engine(access_database_url)
    try:
        plan = build_reconciliation_plan(
            projects_engine=projects_engine,
            service_desk_engine=service_desk_engine,
            access_engine=access_engine,
        )
        applied = False
        if apply:
            if not plan.can_apply:
                report = plan.report_dict(mode="apply", applied=False)
                write_reconciliation_report(report, report_dir)
                raise IdentityMigrationConflict(
                    f"Identity migration has {len(plan.conflicts)} blocking conflict(s)"
                )
            _apply_access(plan, access_engine)
            _apply_service_desk(plan, service_desk_engine)
            applied = True
        report = plan.report_dict(mode="apply" if apply else "dry-run", applied=applied)
        write_reconciliation_report(report, report_dir)
        return report
    finally:
        projects_engine.dispose()
        service_desk_engine.dispose()
        access_engine.dispose()
