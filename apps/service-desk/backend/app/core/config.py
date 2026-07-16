from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PROM Service Desk"
    service_code: str = "service-desk"
    env: str = "development"
    database_url: str = "postgresql+psycopg://service_desk:service_desk@localhost:5433/service_desk"
    jwt_secret: str = "change-me-in-production-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_jwks_url: str | None = None
    access_token_issuer: str = "prom-access"
    frontend_origin: str = "http://localhost:5173"
    storage_dir: str = "storage/service-desk"
    max_attachment_size_bytes: int = 10 * 1024 * 1024
    max_attachments_per_owner: int = 10
    sla_worker_poll_interval_seconds: int = 60
    notification_list_default_limit: int = 30
    notification_list_max_limit: int = 100
    notification_outbox_batch_size: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SERVICE_DESK_",
        extra="ignore",
    )


settings = Settings()
