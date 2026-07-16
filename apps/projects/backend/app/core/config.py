from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Project Showcase SHPIU"
    env: str = "development"
    database_url: str = "postgresql+psycopg://project_showcase:project_showcase@localhost:5432/project_showcase"
    jwt_secret: str = "change-me-in-production-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_jwks_url: str | None = None
    access_token_issuer: str = "prom-access"
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    uploads_dir: str = "storage/uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
