from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AccessSettings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://prom_access:prom_access@access-db:5432/prom_access"
    frontend_origin: str = "http://localhost:5173"
    token_issuer: str = "prom-access"
    token_ttl_seconds: int = 900
    jwt_private_key: str | None = None
    jwt_key_id: str = "local-ephemeral"
    trusted_headers_enabled: bool = False
    trusted_proxy_networks: str = ""
    sso_provider: Literal["mock", "trusted-header", "oidc"] = Field(default="mock", validation_alias="SSO_PROVIDER")
    oidc_enabled: bool = False
    oidc_issuer_url: str | None = Field(default=None, validation_alias="SSO_ISSUER_URL")
    oidc_client_id: str | None = Field(default=None, validation_alias="SSO_CLIENT_ID")
    oidc_client_secret: str | None = Field(default=None, validation_alias="SSO_CLIENT_SECRET")
    oidc_redirect_uri: str | None = Field(default=None, validation_alias="SSO_REDIRECT_URI")
    oidc_scopes: str = Field(default="openid profile email", validation_alias="SSO_SCOPES")
    oidc_allowed_audiences: str = Field(default="", validation_alias="SSO_ALLOWED_AUDIENCES")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="ACCESS_", extra="ignore"
    )

    @field_validator("jwt_private_key", mode="before")
    @classmethod
    def normalize_pem(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        normalized = value.strip().replace("\\n", "\n")
        return normalized or None

    @model_validator(mode="after")
    def validate_security(self) -> "AccessSettings":
        production = self.environment.lower() in {"production", "prod"}
        if production:
            if self.debug:
                raise ValueError("ACCESS_DEBUG must be false in production")
            if not self.jwt_private_key:
                raise ValueError("ACCESS_JWT_PRIVATE_KEY is required in production")
            if self.frontend_origin == "*":
                raise ValueError("ACCESS_FRONTEND_ORIGIN cannot be a wildcard in production")
            if self.sso_provider == "mock":
                raise ValueError("SSO_PROVIDER=mock is not allowed in production")
            if (self.oidc_enabled or self.sso_provider == "oidc") and not all(
                [self.oidc_issuer_url, self.oidc_client_id, self.oidc_client_secret, self.oidc_redirect_uri]
            ):
                raise ValueError("OIDC is enabled but its required configuration is incomplete")
        return self


settings = AccessSettings()
