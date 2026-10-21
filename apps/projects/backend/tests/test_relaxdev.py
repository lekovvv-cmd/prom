from io import BytesIO
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.config import Settings
from app.core.database import SessionLocal
from app.modules.attachments.models import Attachment, AttachmentBlob
from app.modules.attachments.storage import DatabaseStorage
from app.modules.projects.models import Project
from app.modules.users.models import User
from platform_sdk.config import database_url_from_environment
from scripts.outbox_worker import process_batch
from scripts import start
from scripts import seed_pilot
from test_projects_integrity import auth_headers, project_payload
from sqlalchemy import func, select


def test_database_url_fallback_and_psycopg(monkeypatch):
    monkeypatch.delenv("PROJECTS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:secret@db:5432/projects")
    assert (
        database_url_from_environment("PROJECTS", "unused")
        == "postgresql+psycopg://user:secret@db:5432/projects"
    )
    monkeypatch.setenv("PROJECTS_DATABASE_URL", "postgresql://user:secret@other/projects")
    assert (
        database_url_from_environment("PROJECTS", "unused")
        == "postgresql+psycopg://user:secret@other/projects"
    )


def test_projects_settings_use_managed_database_url(monkeypatch):
    monkeypatch.delenv("PROJECTS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:secret@managed/projects")
    assert (
        Settings(_env_file=None).database_url == "postgresql+psycopg://user:secret@managed/projects"
    )


def test_database_attachment_storage_crud(database):
    with SessionLocal() as db:
        store = DatabaseStorage(db)
        key = "test/relaxdev.txt"
        assert (
            store.put(key, BytesIO(b"pilot bytes"))
            == "ea17ab386a27c143fa4acd72658179f52ceec851515e8af96017bad196a82af5"
        )
        db.commit()
    with SessionLocal() as db:
        store = DatabaseStorage(db)
        assert store.exists(key)
        assert store.get(key).read() == b"pilot bytes"
        store.delete(key)
        db.commit()
    with SessionLocal() as db:
        assert not DatabaseStorage(db).exists(key)


def test_database_attachment_download_stays_permission_checked(client, monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "database")
    admin = auth_headers("admin@utmn.ru")
    project = client.post(
        "/api/admin/projects", json=project_payload(f"DB files {uuid4()}"), headers=admin
    )
    assert project.status_code == 201, project.text
    uploaded = client.post(
        f"/api/admin/projects/{project.json()['id']}/attachments",
        files={"file": ("pilot.txt", b"persistent bytes", "text/plain")},
        headers=admin,
    )
    assert uploaded.status_code == 201, uploaded.text
    attachment = uploaded.json()
    with SessionLocal() as db:
        record = db.get(Attachment, UUID(attachment["id"]))
        assert record is not None
        assert db.get(AttachmentBlob, record.storage_key) is not None
    assert client.get(attachment["download_url"]).status_code == 401
    assert client.get(attachment["download_url"], headers=admin).content == b"persistent bytes"
    assert client.delete(attachment["download_url"], headers=admin).status_code == 200
    process_batch(worker_id="relaxdev-db-delete", batch_size=200)
    assert client.get(attachment["download_url"], headers=admin).status_code == 404


def test_pilot_seed_repeated_restart_keeps_existing_data(database):
    seed_pilot.main()
    with SessionLocal() as db:
        before = (
            db.scalar(
                select(func.count()).select_from(User).where(User.email.like("pilot.%@utmn.ru"))
            ),
            db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.title.in_([item["title"] for item in seed_pilot.PROJECTS]))
            ),
        )
    seed_pilot.main()
    with SessionLocal() as db:
        after = (
            db.scalar(
                select(func.count()).select_from(User).where(User.email.like("pilot.%@utmn.ru"))
            ),
            db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.title.in_([item["title"] for item in seed_pilot.PROJECTS]))
            ),
        )
    assert before == after == (12, 4)


def test_worker_skips_migration_and_seed(monkeypatch):
    calls = []
    monkeypatch.setenv("PROJECTS_PROCESS", "worker")
    monkeypatch.setenv("PROM_RUN_MIGRATIONS", "true")
    monkeypatch.setenv("PROM_SEED_PILOT", "true")
    monkeypatch.setattr(start.os, "execvp", lambda *args: calls.append(args))
    monkeypatch.setattr(
        start.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    start.main()
    assert calls == [("python", ["python", "-m", "scripts.worker"])]


def test_web_startup_orders_migration_seed_and_port(monkeypatch):
    calls = []
    monkeypatch.setenv("PROJECTS_PROCESS", "web")
    monkeypatch.setenv("PROM_RUN_MIGRATIONS", "true")
    monkeypatch.setenv("PROM_SEED_PILOT", "true")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setattr(start.os, "execvp", lambda *args: calls.append(args))
    monkeypatch.setattr(
        start.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    start.main()
    assert calls[0][0][0] == ["python", "-m", "alembic", "upgrade", "head"]
    assert calls[1][0][0] == ["python", "scripts/seed_pilot.py"]
    assert calls[2][1][-1] == "8080"
