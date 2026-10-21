from __future__ import annotations

from pathlib import Path
from typing import Literal
from pydantic import Field

from platform_sdk.config import (
    database_url_from_environment,
    normalize_postgres_url,
    is_insecure_secret,
    is_production_environment,
    parse_nonempty_csv,
    validate_production_database_url,
)
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AccessSettings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    database_url: str = Field(
        default_factory=lambda: database_url_from_environment(
            "ACCESS", "postgresql+psycopg://prom_access:prom_access@access-db:5432/prom_access"
        )
    )
    token_issuer: str = "prom-access"
    token_audiences: str = "projects,service-desk"
    token_ttl_seconds: int = 900
    jwt_private_key: str | None = None
    jwt_private_key_file: str | None = None
    jwt_key_id: str = "local-ephemeral"
    session_cookie_name: str = "prom_session"
    session_csrf_cookie_name: str = "prom_csrf"
    session_same_site: Literal["lax", "strict"] = "lax"
    session_idle_ttl_seconds: int = 604800
    session_absolute_ttl_seconds: int = 2592000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ACCESS_",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("jwt_private_key", mode="before")
    @classmethod
    def normalize_pem(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        normalized = value.strip().replace("\\n", "\n")
        return normalized or None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return normalize_postgres_url(value)

    @model_validator(mode="after")
    def validate_security(self) -> "AccessSettings":
        production = is_production_environment(self.environment)
        secure_runtime = production or self.environment.lower() == "pilot"
        if secure_runtime:
            validate_production_database_url(
                self.database_url,
                variable_name="ACCESS_DATABASE_URL",
            )
            if is_insecure_secret(self.jwt_private_key) and not self.jwt_private_key_file:
                raise ValueError(
                    "ACCESS_JWT_PRIVATE_KEY or ACCESS_JWT_PRIVATE_KEY_FILE must be configured in secure environments"
                )
            if not self.jwt_key_id.strip() or self.jwt_key_id == "local-ephemeral":
                raise ValueError("ACCESS_JWT_KEY_ID must identify the signing key")
            if not self.token_issuer.strip():
                raise ValueError("ACCESS_TOKEN_ISSUER is required in secure environments")
            if not parse_nonempty_csv(self.token_audiences):
                raise ValueError("ACCESS_TOKEN_AUDIENCES is required in secure environments")
            if self.debug:
                raise ValueError("ACCESS_DEBUG must be false in secure environments")
        if self.session_idle_ttl_seconds > self.session_absolute_ttl_seconds:
            raise ValueError("Session idle TTL cannot exceed absolute TTL")
        return self

    @property
    def token_audience_values(self) -> tuple[str, ...]:
        return parse_nonempty_csv(self.token_audiences)

    @property
    def signing_private_key(self) -> str | None:
        if self.jwt_private_key:
            return self.jwt_private_key
        if self.jwt_private_key_file:
            return Path(self.jwt_private_key_file).read_text(encoding="utf-8")
        return None

    @property
    def secure_cookies(self) -> bool:
        return is_production_environment(self.environment) or self.environment.lower() == "pilot"


settings = AccessSettings()
