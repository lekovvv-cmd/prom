from platform_sdk.config import (
    is_production_environment,
    validate_production_database_url,
)
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Project Showcase SHPIU"
    env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://project_showcase:project_showcase@localhost:5432/project_showcase"
    access_jwks_url: str | None = None
    access_token_issuer: str = "prom-access"
    access_token_audience: str = "projects"
    uploads_dir: str = "storage/uploads"
    max_attachment_size_bytes: int = 10 * 1024 * 1024
    max_attachments_per_owner: int = 10
    attachment_orphan_grace_seconds: int = 3600
    worker_metrics_port: int = 9100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PROJECTS_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if is_production_environment(self.env):
            validate_production_database_url(
                self.database_url,
                variable_name="PROJECTS_DATABASE_URL",
            )
            if self.debug:
                raise ValueError("PROJECTS_DEBUG must be false in production")
            if not self.access_jwks_url:
                raise ValueError("PROJECTS_ACCESS_JWKS_URL is required in production")
            if not self.access_token_issuer.strip():
                raise ValueError("PROJECTS_ACCESS_TOKEN_ISSUER is required in production")
            if not self.access_token_audience.strip():
                raise ValueError("PROJECTS_ACCESS_TOKEN_AUDIENCE is required in production")
        return self


settings = Settings()
