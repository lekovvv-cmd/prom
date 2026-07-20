from __future__ import annotations

import pytest

from platform_sdk.config import (
    has_cors_wildcard,
    is_insecure_secret,
    parse_nonempty_csv,
    validate_production_database_url,
)


def test_database_guard_requires_postgres_with_password() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_production_database_url(
            "sqlite:///production.db",
            variable_name="DATABASE_URL",
        )

    with pytest.raises(ValueError, match="non-empty password"):
        validate_production_database_url(
            "postgresql+psycopg://prom@db/prom",
            variable_name="DATABASE_URL",
        )


def test_security_config_helpers_normalize_values() -> None:
    assert has_cors_wildcard("https://prom.example, *")
    assert is_insecure_secret("change-me-in-production-at-least-32-bytes")
    assert parse_nonempty_csv("projects, service-desk, ") == (
        "projects",
        "service-desk",
    )
