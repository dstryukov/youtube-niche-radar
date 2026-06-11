from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://redis:6379/0"
    youtube_api_key: str
    openai_api_key: str | None = None

    sync_recent_video_limit: int = 50
    default_sync_limit: int = 50
    quota_warn_daily_units: int = 8_000

    api_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
