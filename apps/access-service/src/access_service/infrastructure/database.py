from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from access_service.bootstrap.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5, pool_timeout=30)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session

