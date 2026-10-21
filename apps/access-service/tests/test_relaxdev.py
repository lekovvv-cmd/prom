import importlib.util
from pathlib import Path

from platform_sdk.config import database_url_from_environment
from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import Base, PlatformUser
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker


def load_access_script(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"access_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


start = load_access_script("start")
seed_pilot = load_access_script("seed_pilot")


def test_database_url_fallback_and_override(monkeypatch):
    monkeypatch.delenv("ACCESS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db/access")
    assert database_url_from_environment("ACCESS", "unused") == "postgresql+psycopg://u:p@db/access"
    monkeypatch.setenv("ACCESS_DATABASE_URL", "postgresql://u:p@other/access")
    assert (
        database_url_from_environment("ACCESS", "unused") == "postgresql+psycopg://u:p@other/access"
    )


def test_access_settings_use_managed_database_url(monkeypatch):
    monkeypatch.delenv("ACCESS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@managed/access")
    assert AccessSettings(_env_file=None).database_url == "postgresql+psycopg://u:p@managed/access"


def test_access_startup_migration_seed_and_port(monkeypatch):
    calls = []
    monkeypatch.setenv("PROM_RUN_MIGRATIONS", "true")
    monkeypatch.setenv("PROM_SEED_PILOT", "true")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setattr(
        start.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    monkeypatch.setattr(start.os, "execvp", lambda *args: calls.append(args))
    start.main()
    assert calls[0][0][0] == ["python", "scripts/init_db.py"]
    assert calls[1][0][0] == ["python", "scripts/seed_pilot.py"]
    assert calls[2][1][-1] == "8080"


def test_access_pilot_seed_is_idempotent(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(seed_pilot, "SessionLocal", sessionmaker(bind=engine))
    seed_pilot.main()
    seed_pilot.main()
    with sessionmaker(bind=engine)() as db:
        assert db.scalar(select(func.count()).select_from(PlatformUser)) == 12
    engine.dispose()
