from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url


@dataclass(frozen=True, slots=True)
class DatabasePoolConfig:
    application_name: str
    pool_size: int = 5
    max_overflow: int = 5
    pool_timeout_seconds: int = 30
    pool_recycle_seconds: int = 1800
    statement_timeout_ms: int = 30_000
    pool_pre_ping: bool = True

    @property
    def maximum_connections(self) -> int:
        return self.pool_size + self.max_overflow


def create_platform_engine(database_url: str, config: DatabasePoolConfig) -> Engine:
    url = make_url(database_url)
    options: dict[str, Any] = {
        "pool_pre_ping": config.pool_pre_ping,
        "pool_recycle": config.pool_recycle_seconds,
    }

    if not url.drivername.startswith("sqlite"):
        options.update(
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout_seconds,
        )

    if url.drivername.startswith("postgresql"):
        options["connect_args"] = {
            "options": (
                f"-c statement_timeout={config.statement_timeout_ms} "
                f"-c application_name={config.application_name}"
            )
        }

    return create_engine(database_url, **options)


def pool_metrics(engine: Engine, config: DatabasePoolConfig) -> dict[str, int | str]:
    pool = engine.pool

    def read_metric(name: str) -> int:
        value = getattr(pool, name, None)
        if not callable(value):
            return 0
        try:
            return int(value())
        except (NotImplementedError, TypeError):
            return 0

    return {
        "application_name": config.application_name,
        "configured_pool_size": config.pool_size,
        "configured_max_overflow": config.max_overflow,
        "configured_maximum_connections": config.maximum_connections,
        "checked_in": read_metric("checkedin"),
        "checked_out": read_metric("checkedout"),
        "overflow": read_metric("overflow"),
    }
