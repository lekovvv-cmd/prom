from platform_sdk.config import (
    has_cors_wildcard,
    is_insecure_secret,
    is_production_environment,
    validate_production_database_url,
)
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-in-production-at-least-32-bytes"


class Settings(BaseSettings):
    app_name: str = "Project Showcase SHPIU"
    env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://project_showcase:project_showcase@localhost:5432/project_showcase"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_jwks_url: str | None = None
    access_token_issuer: str = "prom-access"
    access_token_audience: str = "projects"
    access_jwks_cache_ttl_seconds: int = 300
    access_jwks_stale_if_error_seconds: int = 3600
    access_clock_skew_seconds: int = 30
    allow_legacy_tokens: bool = False
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    uploads_dir: str = "storage/uploads"
    storage_backend: str = "local"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region_name: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    antivirus_backend: str = "noop"
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    max_attachment_size_bytes: int = 10 * 1024 * 1024
    max_attachments_per_owner: int = 10
    attachment_orphan_grace_seconds: int = 3600
    worker_metrics_port: int = 9100
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    db_statement_timeout_ms: int = 30_000
    db_application_name: str = "prom-projects-api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PROJECTS_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.storage_backend not in {"local", "s3"}:
            raise ValueError("PROJECTS_STORAGE_BACKEND must be local or s3")
        if self.storage_backend == "s3" and not self.s3_bucket:
            raise ValueError("PROJECTS_S3_BUCKET is required when S3 storage is enabled")
        if self.antivirus_backend not in {"noop", "clamav"}:
            raise ValueError("PROJECTS_ANTIVIRUS_BACKEND must be noop or clamav")

        if is_production_environment(self.env):
            validate_production_database_url(
                self.database_url,
                variable_name="PROJECTS_DATABASE_URL",
            )
            if self.debug:
                raise ValueError("PROJECTS_DEBUG must be false in production")
            if is_insecure_secret(
                self.jwt_secret,
                known_defaults=(DEFAULT_JWT_SECRET,),
            ):
                raise ValueError("PROJECTS_JWT_SECRET cannot use a default value in production")
            if self.allow_legacy_tokens:
                raise ValueError("PROJECTS_ALLOW_LEGACY_TOKENS must be false in production")
            if not self.access_jwks_url:
                raise ValueError("PROJECTS_ACCESS_JWKS_URL is required in production")
            if not self.access_token_issuer.strip():
                raise ValueError("PROJECTS_ACCESS_TOKEN_ISSUER is required in production")
            if not self.access_token_audience.strip():
                raise ValueError("PROJECTS_ACCESS_TOKEN_AUDIENCE is required in production")
            if has_cors_wildcard(self.frontend_origin):
                raise ValueError("PROJECTS_FRONTEND_ORIGIN cannot be a wildcard in production")
            if self.antivirus_backend == "noop":
                raise ValueError("PROJECTS_ANTIVIRUS_BACKEND=noop is not allowed in production")
        return self


settings = Settings()
