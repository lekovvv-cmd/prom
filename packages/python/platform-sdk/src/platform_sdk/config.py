from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        if self.environment.lower() in {"production", "prod"}:
            if self.debug:
                raise ValueError("PLATFORM_DEBUG must be false in production")
            if self.frontend_origin == "*":
                raise ValueError("PLATFORM_FRONTEND_ORIGIN cannot be a wildcard in production")
        return self

