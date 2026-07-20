from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.modules.platform.models import (
    ProjectAuditEvent,
    ProjectIdempotencyRecord,
    ProjectOutboxEvent,
)
from app.modules.users.repository import UserRepository
from scripts.attachment_cleanup_worker import cleanup_once
from scripts.outbox_worker import process_batch
from sqlalchemy import select


def auth_headers(email: str) -> dict[str, str]:
    with SessionLocal() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None
        token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}


def project_payload(title: str) -> dict[str, object]:
    return {
        "title": title,
        "short_description": "Integrity test project.",
        "description": "Checks application transaction guarantees.",
        "goal": "Verify idempotency, audit and outbox.",
        "expected_result": "One durable project and one command result.",
        "project_type": "strategic",
        "priority": "medium",
        "status": "active",
        "start_date": None,
        "end_date": None,
        "responsible_user_id": None,
        "contact_email": "project.manager@utmn.ru",
        "required_competencies": "Testing",
        "planned_tasks": "Run integrity tests",
    }


def test_create_project_is_idempotent_and_writes_audit_and_outbox(client):
    headers = {
        **auth_headers("admin@utmn.ru"),
        "Idempotency-Key": f"create-project-{uuid4()}",
    }
    payload = project_payload(f"Idempotent project {uuid4()}")

    first = client.post("/api/admin/projects", json=payload, headers=headers)
    second = client.post("/api/admin/projects", json=payload, headers=headers)

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]

    conflicting = client.post(
        "/api/admin/projects",
        json={**payload, "title": f"Different payload {uuid4()}"},
        headers=headers,
    )
    assert conflicting.status_code == 409
    assert conflicting.headers["content-type"].startswith("application/problem+json")

    project_id = first.json()["id"]
    with SessionLocal() as db:
        audits = list(
            db.scalars(
                select(ProjectAuditEvent).where(
                    ProjectAuditEvent.object_id == project_id,
                    ProjectAuditEvent.action == "project.created",
                )
            )
        )
        events = list(
            db.scalars(
                select(ProjectOutboxEvent).where(
                    ProjectOutboxEvent.aggregate_id == project_id,
                    ProjectOutboxEvent.event_type == "ProjectCreated",
                )
            )
        )
        records = list(
            db.scalars(
                select(ProjectIdempotencyRecord).where(
                    ProjectIdempotencyRecord.idempotency_key
                    == headers["Idempotency-Key"]
                )
            )
        )
    assert len(audits) == 1
    assert len(events) == 1
    assert len(records) == 1


def test_project_update_rejects_stale_if_match(client):
    headers = auth_headers("admin@utmn.ru")
    created = client.post(
        "/api/admin/projects",
        json=project_payload(f"Versioned project {uuid4()}"),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    version = created.json()["version"]

    updated = client.patch(
        f"/api/admin/projects/{project_id}",
        json={"title": f"Updated versioned project {uuid4()}"},
        headers={**headers, "If-Match": str(version)},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == version + 1

    stale = client.patch(
        f"/api/admin/projects/{project_id}",
        json={"title": f"Stale project update {uuid4()}"},
        headers={**headers, "If-Match": str(version)},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "CONFLICT_DETECTED"


def test_attachment_is_streamed_validated_authorized_and_audited(client):
    admin = auth_headers("admin@utmn.ru")
    employee = auth_headers("employee@utmn.ru")
    created = client.post(
        "/api/admin/projects",
        json=project_payload(f"Attachment security {uuid4()}"),
        headers=admin,
    )
    project_id = created.json()["id"]

    invalid = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
        headers=admin,
    )
    assert invalid.status_code == 422

    uploaded = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        files={"file": ("../safe.txt", b"safe attachment", "text/plain")},
        headers=admin,
    )
    assert uploaded.status_code == 201, uploaded.text
    body = uploaded.json()
    assert body["file_name"] == "safe.txt"
    assert len(body["checksum"]) == 64
    assert body["status"] == "available"

    markdown = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        files={"file": ("plan.md", b"# safe plan", "text/markdown")},
        headers=admin,
    )
    assert markdown.status_code == 201, markdown.text
    assert markdown.json()["content_type_detected"] == "text/markdown"

    anonymous = client.get(body["download_url"])
    assert anonymous.status_code == 401
    downloaded = client.get(body["download_url"], headers=employee)
    assert downloaded.status_code == 200
    assert downloaded.content == b"safe attachment"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["cache-control"] == "private, no-store"

    deleted = client.delete(body["download_url"], headers=admin)
    assert deleted.status_code == 200
    assert client.get(body["download_url"], headers=admin).status_code == 404

    with SessionLocal() as db:
        actions = {
            action
            for action in db.scalars(
                select(ProjectAuditEvent.action).where(
                    ProjectAuditEvent.object_id == body["id"]
                )
            )
        }
    assert {
        "project.attachment_uploaded",
        "project.attachment_downloaded",
        "project.attachment_deleted",
    }.issubset(actions)


def test_outbox_worker_and_orphan_cleanup_are_idempotent(client, monkeypatch):
    headers = auth_headers("admin@utmn.ru")
    created = client.post(
        "/api/admin/projects",
        json=project_payload(f"Outbox worker {uuid4()}"),
        headers=headers,
    )
    project_id = created.json()["id"]

    assert process_batch(worker_id="pytest", batch_size=200) >= 1
    process_batch(worker_id="pytest", batch_size=200)
    with SessionLocal() as db:
        statuses = set(
            db.scalars(
                select(ProjectOutboxEvent.status).where(
                    ProjectOutboxEvent.aggregate_id == project_id
                )
            )
        )
    assert statuses == {"processed"}

    from app.core.config import settings

    monkeypatch.setattr(settings, "attachment_orphan_grace_seconds", 0)
    root = Path(settings.uploads_dir).resolve()
    orphan = root / "orphan" / f"{uuid4()}.txt"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("orphan", encoding="utf-8")
    os.utime(orphan, (0, 0))

    assert cleanup_once() >= 1
    assert not orphan.exists()
