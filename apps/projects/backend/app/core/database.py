from collections.abc import Generator
from datetime import UTC, datetime

from platform_sdk.database import DatabasePoolConfig, create_platform_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


pool_config = DatabasePoolConfig(application_name="prom-projects-api")
engine = create_platform_engine(settings.database_url, pool_config)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_session() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        if db.in_transaction():
            db.rollback()
        db.close()
