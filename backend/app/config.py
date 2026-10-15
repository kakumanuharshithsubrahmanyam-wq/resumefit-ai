from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else None,
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

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_openai_api_key(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def openai_configured(self) -> bool:
        """True when AI is enabled and a non-empty OpenAI key is present."""
        return self.ai_enabled and bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
