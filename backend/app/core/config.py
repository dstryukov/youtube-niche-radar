from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://redis:6379/0"
    youtube_api_key: str
    openai_api_key: str | None = None  # deprecated, use llm_api_key / groq_api_key / gemini_api_key

    sync_recent_video_limit: int = 50
    default_sync_limit: int = 50
    quota_warn_daily_units: int = 8_000

    api_env: str = "development"
    log_level: str = "INFO"

    # --- LLM / AI Classification ---
    llm_provider: str = "groq"  # groq | gemini
    llm_api_key: str | None = None
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    llm_model: str = "llama-3.3-70b-versatile"
    llm_prompt_version: str = "format-v4"
    llm_temperature: float = 0.1
    llm_max_retries: int = 2

    @field_validator("llm_provider")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        return v.lower()

    @field_validator("llm_model")
    @classmethod
    def strip_model(cls, v: str) -> str:
        return v.strip()


settings = Settings()
