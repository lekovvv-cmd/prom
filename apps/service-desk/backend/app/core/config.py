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
    app_name: str = "PROM Service Desk"
    service_code: str = "service-desk"
    env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://service_desk:service_desk@localhost:5433/service_desk"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_jwks_url: str | None = None
    access_token_issuer: str = "prom-access"
    access_token_audience: str = "service-desk"
    access_jwks_cache_ttl_seconds: int = 300
    access_jwks_stale_if_error_seconds: int = 3600
    access_clock_skew_seconds: int = 30
    allow_legacy_tokens: bool = False
    frontend_origin: str = "http://localhost:5173"
    storage_dir: str = "storage/service-desk"
    storage_backend: str = "filesystem"
    s3_endpoint: str | None = None
    s3_bucket: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str | None = None
    storage_signed_url_ttl_seconds: int = 60
    antivirus_backend: str = "noop"
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    clamav_timeout_seconds: float = 10.0
    max_attachment_size_bytes: int = 10 * 1024 * 1024
    max_attachments_per_owner: int = 10
    attachment_orphan_grace_seconds: int = 3600
    attachment_rejected_retention_days: int = 7
    worker_metrics_port: int = 9100
    sla_worker_poll_interval_seconds: int = 60
    notification_list_default_limit: int = 30
    notification_list_max_limit: int = 100
    notification_outbox_batch_size: int = 50
    notification_outbox_max_attempts: int = 8
    notification_outbox_retry_base_seconds: int = 5
    notification_outbox_retry_max_seconds: int = 3600
    notification_outbox_cleanup_batch_size: int = 500
    notification_outbox_processed_retention_days: int = 30
    notification_outbox_dead_retention_days: int = 90
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    db_statement_timeout_ms: int = 30_000
    db_application_name: str = "prom-service-desk-api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SERVICE_DESK_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.storage_backend not in {"filesystem", "local", "s3"}:
            raise ValueError(
                "SERVICE_DESK_STORAGE_BACKEND must be filesystem, local, or s3"
            )
        if self.storage_backend == "s3" and not self.s3_bucket:
            raise ValueError(
                "SERVICE_DESK_S3_BUCKET is required when S3 storage is enabled"
            )
        if self.antivirus_backend not in {"noop", "clamav"}:
            raise ValueError("SERVICE_DESK_ANTIVIRUS_BACKEND must be noop or clamav")

        if is_production_environment(self.env):
            validate_production_database_url(
                self.database_url,
                variable_name="SERVICE_DESK_DATABASE_URL",
            )
            if self.debug:
                raise ValueError("SERVICE_DESK_DEBUG must be false in production")
            if is_insecure_secret(
                self.jwt_secret,
                known_defaults=(DEFAULT_JWT_SECRET,),
            ):
                raise ValueError(
                    "SERVICE_DESK_JWT_SECRET cannot use a default value in production"
                )
            if self.allow_legacy_tokens:
                raise ValueError(
                    "SERVICE_DESK_ALLOW_LEGACY_TOKENS must be false in production"
                )
            if not self.access_jwks_url:
                raise ValueError("SERVICE_DESK_ACCESS_JWKS_URL is required in production")
            if not self.access_token_issuer.strip():
                raise ValueError(
                    "SERVICE_DESK_ACCESS_TOKEN_ISSUER is required in production"
                )
            if not self.access_token_audience.strip():
                raise ValueError(
                    "SERVICE_DESK_ACCESS_TOKEN_AUDIENCE is required in production"
                )
            if has_cors_wildcard(self.frontend_origin):
                raise ValueError(
                    "SERVICE_DESK_FRONTEND_ORIGIN cannot be a wildcard in production"
                )
            if self.antivirus_backend == "noop":
                raise ValueError(
                    "SERVICE_DESK_ANTIVIRUS_BACKEND=noop is not allowed in production"
                )
        return self


settings = Settings()
