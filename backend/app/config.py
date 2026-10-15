from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ResumeFit AI"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = "sqlite:///./data/resumefit.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = 5 * 1024 * 1024
    ai_enabled: bool = True
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = 30.0
    ai_max_input_chars: int = 12000
    environment: str = "development"
    rate_limit_requests_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
