from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PROM Service Desk"
    service_code: str = "service-desk"
    env: str = "development"
    database_url: str = "postgresql+psycopg://service_desk:service_desk@localhost:5433/service_desk"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SERVICE_DESK_",
        extra="ignore",
    )


settings = Settings()
