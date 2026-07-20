from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "env": "production",
        "database_url": "postgresql+psycopg://projects:secret@db/projects",
        "jwt_secret": "projects-production-secret-with-32-bytes",
        "access_jwks_url": "https://prom.example/api/access/v1/.well-known/jwks.json",
        "access_token_issuer": "https://prom.example/access",
        "access_token_audience": "projects",
        "allow_legacy_tokens": False,
        "frontend_origin": "https://prom.example",
        "antivirus_backend": "clamav",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"database_url": "sqlite:///production.db"}, "PostgreSQL"),
        ({"database_url": "postgresql+psycopg://projects@db/projects"}, "non-empty password"),
        ({"debug": True}, "PROJECTS_DEBUG"),
        (
            {"jwt_secret": "change-me-in-production-at-least-32-bytes"},
            "PROJECTS_JWT_SECRET",
        ),
        ({"allow_legacy_tokens": True}, "PROJECTS_ALLOW_LEGACY_TOKENS"),
        ({"access_jwks_url": None}, "PROJECTS_ACCESS_JWKS_URL"),
        ({"access_token_issuer": ""}, "PROJECTS_ACCESS_TOKEN_ISSUER"),
        ({"access_token_audience": ""}, "PROJECTS_ACCESS_TOKEN_AUDIENCE"),
        ({"frontend_origin": "https://prom.example,*"}, "PROJECTS_FRONTEND_ORIGIN"),
        ({"antivirus_backend": "noop"}, "PROJECTS_ANTIVIRUS_BACKEND=noop"),
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

    assert configured.access_token_audience == "projects"
