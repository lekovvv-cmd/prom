from __future__ import annotations

from typing import Literal

from platform_sdk.config import (
    has_cors_wildcard,
    is_insecure_secret,
    is_production_environment,
    parse_nonempty_csv,
    validate_production_database_url,
)
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AccessSettings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://prom_access:prom_access@access-db:5432/prom_access"
    frontend_origin: str = "http://localhost:5173"
    token_issuer: str = "prom-access"
    token_audiences: str = "projects,service-desk"
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
    oidc_jwks_cache_ttl_seconds: int = Field(default=300, validation_alias="SSO_JWKS_CACHE_TTL")
    oidc_post_logout_redirect_uri: str | None = Field(
        default=None,
        validation_alias="SSO_POST_LOGOUT_REDIRECT_URI",
    )
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    db_statement_timeout_ms: int = 30_000
    db_application_name: str = "prom-access-api"

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

    @model_validator(mode="after")
    def validate_security(self) -> "AccessSettings":
        production = is_production_environment(self.environment)
        if production:
            validate_production_database_url(
                self.database_url,
                variable_name="ACCESS_DATABASE_URL",
            )
            if self.debug:
                raise ValueError("ACCESS_DEBUG must be false in production")
            if is_insecure_secret(self.jwt_private_key):
                raise ValueError(
                    "ACCESS_JWT_PRIVATE_KEY must be explicitly configured in production"
                )
            if not self.jwt_key_id.strip() or self.jwt_key_id == "local-ephemeral":
                raise ValueError("ACCESS_JWT_KEY_ID must identify the production signing key")
            if has_cors_wildcard(self.frontend_origin):
                raise ValueError("ACCESS_FRONTEND_ORIGIN cannot be a wildcard in production")
            if not self.token_issuer.strip():
                raise ValueError("ACCESS_TOKEN_ISSUER is required in production")
            if not parse_nonempty_csv(self.token_audiences):
                raise ValueError("ACCESS_TOKEN_AUDIENCES is required in production")
            if self.sso_provider == "mock":
                raise ValueError("SSO_PROVIDER=mock is not allowed in production")
            if (self.oidc_enabled or self.sso_provider == "oidc") and not all(
                [self.oidc_issuer_url, self.oidc_client_id, self.oidc_client_secret, self.oidc_redirect_uri]
            ):
                raise ValueError("OIDC is enabled but its required configuration is incomplete")
        if self.oidc_jwks_cache_ttl_seconds < 30:
            raise ValueError("SSO_JWKS_CACHE_TTL must be at least 30 seconds")
        return self

    @property
    def token_audience_values(self) -> tuple[str, ...]:
        return parse_nonempty_csv(self.token_audiences)


settings = AccessSettings()
