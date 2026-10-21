from __future__ import annotations

import os
from sqlalchemy.engine import make_url

DEFAULT_SECRET_MARKERS = (
    "change-me",
    "replace-me",
    "example-secret",
    "development-secret",
)


def database_url_from_environment(prefix: str, default: str) -> str:
    """Prefer a service override, then a PaaS managed DATABASE_URL."""
    value = os.getenv(f"{prefix}_DATABASE_URL") or os.getenv("DATABASE_URL") or default
    return normalize_postgres_url(value)


def normalize_postgres_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


def is_production_environment(environment: str) -> bool:
    return environment.strip().lower() in {"production", "prod"}


def validate_production_database_url(database_url: str, *, variable_name: str) -> None:
    try:
        url = make_url(database_url)
    except Exception as exc:
        raise ValueError(f"{variable_name} must be a valid database URL") from exc
    if not url.drivername.startswith("postgresql"):
        raise ValueError(f"{variable_name} must use PostgreSQL in production")
    password = url.password
    if not isinstance(password, str) or not password.strip():
        raise ValueError(f"{variable_name} must include a non-empty password in production")


def is_insecure_secret(secret: str | None, *, known_defaults: tuple[str, ...] = ()) -> bool:
    if not isinstance(secret, str) or not secret.strip():
        return True
    normalized = secret.strip().lower()
    return normalized in {value.lower() for value in known_defaults} or any(
        marker in normalized for marker in DEFAULT_SECRET_MARKERS
    )


def parse_nonempty_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
