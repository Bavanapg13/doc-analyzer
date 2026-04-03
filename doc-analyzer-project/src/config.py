from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(
        default="sk_track2_987654321",
        validation_alias="API_KEY",
    )
    analysis_provider: Literal["auto", "openai", "heuristic"] = Field(
        default="auto",
        validation_alias="ANALYSIS_PROVIDER",
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    openai_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias="OPENAI_MODEL",
    )
    tesseract_cmd: str | None = Field(
        default=None,
        validation_alias="TESSERACT_CMD",
    )
    max_file_size_mb: int = Field(
        default=10,
        validation_alias="MAX_FILE_SIZE_MB",
    )
    max_analysis_characters: int = Field(
        default=15000,
        validation_alias="MAX_ANALYSIS_CHARACTERS",
    )
    celery_broker_url: str = Field(
        default="memory://",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str = Field(
        default="cache+memory://",
        validation_alias="CELERY_RESULT_BACKEND",
    )
    celery_task_always_eager: bool = Field(
        default=True,
        validation_alias="CELERY_TASK_ALWAYS_EAGER",
    )
    celery_result_timeout_seconds: int = Field(
        default=120,
        validation_alias="CELERY_RESULT_TIMEOUT_SECONDS",
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
