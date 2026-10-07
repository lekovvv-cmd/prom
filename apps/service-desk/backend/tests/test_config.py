from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "env": "production",
        "database_url": "postgresql+psycopg://service_desk:secret@db/service_desk",
        "access_jwks_url": "https://prom.example/api/access/v1/.well-known/jwks.json",
        "access_token_issuer": "https://prom.example/access",
        "access_token_audience": "service-desk",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"database_url": "sqlite:///production.db"}, "PostgreSQL"),
        (
            {"database_url": "postgresql+psycopg://service_desk@db/service_desk"},
            "non-empty password",
        ),
        ({"debug": True}, "SERVICE_DESK_DEBUG"),
        ({"access_jwks_url": None}, "SERVICE_DESK_ACCESS_JWKS_URL"),
        ({"access_token_issuer": ""}, "SERVICE_DESK_ACCESS_TOKEN_ISSUER"),
        ({"access_token_audience": ""}, "SERVICE_DESK_ACCESS_TOKEN_AUDIENCE"),
    ],
)
def test_production_settings_reject_unsafe_configuration(
    override: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        production_settings(**override)


def test_production_settings_accept_safe_configuration() -> None:
    configured = production_settings()

    assert configured.access_token_audience == "service-desk"
