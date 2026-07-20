from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

DEFAULT_SECRET_MARKERS = (
    "change-me",
    "replace-me",
    "example-secret",
    "development-secret",
)


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


def has_cors_wildcard(origins: str) -> bool:
    return any(origin.strip() == "*" for origin in origins.split(","))


def is_insecure_secret(secret: str | None, *, known_defaults: tuple[str, ...] = ()) -> bool:
    if not isinstance(secret, str) or not secret.strip():
        return True
    normalized = secret.strip().lower()
    return normalized in {value.lower() for value in known_defaults} or any(
        marker in normalized for marker in DEFAULT_SECRET_MARKERS
    )


def parse_nonempty_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


class PlatformSettings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    frontend_origin: str = "http://localhost:5173"
    internal_token_issuer: str = "prom-access"
    internal_token_audience: str = "prom-platform"
    internal_token_ttl_seconds: int = 900

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_production_safety(self) -> "PlatformSettings":
        if is_production_environment(self.environment):
            if self.debug:
                raise ValueError("PLATFORM_DEBUG must be false in production")
            if has_cors_wildcard(self.frontend_origin):
                raise ValueError("PLATFORM_FRONTEND_ORIGIN cannot be a wildcard in production")
            if not self.internal_token_issuer.strip():
                raise ValueError("PLATFORM_INTERNAL_TOKEN_ISSUER is required in production")
            if not self.internal_token_audience.strip():
                raise ValueError("PLATFORM_INTERNAL_TOKEN_AUDIENCE is required in production")
        return self
