"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for GoldForecaster backend."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    fred_api_key: str = Field(default="", validation_alias="FRED_API_KEY")
    database_path: str = Field(
        default="data/goldforecaster.db",
        validation_alias="DATABASE_PATH",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias="GEMINI_MODEL",
    )
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    gemini_request_delay_seconds: float = Field(
        default=10.0,
        validation_alias="GEMINI_REQUEST_DELAY_SECONDS",
    )
    summarize_batch_limit: int = Field(
        default=5,
        validation_alias="SUMMARIZE_BATCH_LIMIT",
    )
    forecast_news_limit: int = Field(default=10)

    @property
    def database_file(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
