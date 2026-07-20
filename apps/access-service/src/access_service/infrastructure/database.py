from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from access_service.bootstrap.config import settings
from platform_sdk.database import DatabasePoolConfig, create_platform_engine


pool_config = DatabasePoolConfig(
    application_name=settings.db_application_name,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout_seconds=settings.db_pool_timeout_seconds,
    pool_recycle_seconds=settings.db_pool_recycle_seconds,
    statement_timeout_ms=settings.db_statement_timeout_ms,
)
engine = create_platform_engine(settings.database_url, pool_config)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
