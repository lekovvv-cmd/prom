from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from access_service.bootstrap.config import settings
from platform_sdk.database import DatabasePoolConfig, create_platform_engine


pool_config = DatabasePoolConfig(application_name="prom-access-api")
engine = create_platform_engine(settings.database_url, pool_config)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
