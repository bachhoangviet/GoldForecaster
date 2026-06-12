"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_SUMMARIZE_MODELS = (
    "gemini-3.1-flash-lite,gemma-4-26b,gemma-4-31b,"
    "gemini-3.5-flash,gemini-3-flash,"
    "gemini-2.5-flash-lite,gemini-2.5-flash"
)
DEFAULT_FORECAST_MODELS = (
    "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash"
)


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
    gemini_summarize_model: str = Field(
        default="gemini-3.1-flash-lite",
        validation_alias="GEMINI_SUMMARIZE_MODEL",
    )
    gemini_summarize_models: str = Field(
        default="",
        validation_alias="GEMINI_SUMMARIZE_MODELS",
    )
    gemini_forecast_model: str = Field(
        default="gemini-3.5-flash",
        validation_alias="GEMINI_FORECAST_MODEL",
    )
    gemini_forecast_models: str = Field(
        default="",
        validation_alias="GEMINI_FORECAST_MODELS",
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
        default=8.0,
        validation_alias="GEMINI_REQUEST_DELAY_SECONDS",
    )
    gemini_rate_limit_cooldown_seconds: float = Field(
        default=30.0,
        validation_alias="GEMINI_RATE_LIMIT_COOLDOWN_SECONDS",
    )
    gemini_model_cooldown_seconds: float = Field(
        default=300.0,
        validation_alias="GEMINI_MODEL_COOLDOWN_SECONDS",
    )
    summarize_batch_limit: int = Field(
        default=100,
        validation_alias="SUMMARIZE_BATCH_LIMIT",
    )
    forecast_news_limit: int = Field(default=10)
    clear_stale_articles_on_summarize: bool = Field(
        default=True,
        validation_alias="CLEAR_STALE_ARTICLES_ON_SUMMARIZE",
    )
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", validation_alias="TELEGRAM_CHAT_ID")
    daily_job_hour: int = Field(default=7, validation_alias="DAILY_JOB_HOUR")
    daily_job_minute: int = Field(default=0, validation_alias="DAILY_JOB_MINUTE")
    daily_job_timezone: str = Field(
        default="Asia/Ho_Chi_Minh",
        validation_alias="DAILY_JOB_TIMEZONE",
    )

    @property
    def effective_summarize_model(self) -> str:
        return self.effective_summarize_models[0]

    @property
    def effective_forecast_model(self) -> str:
        return self.effective_forecast_models[0]

    @property
    def effective_summarize_models(self) -> list[str]:
        from src.backend.adapters.gemini_model_pool import parse_model_chain

        raw = self.gemini_summarize_models.strip() or DEFAULT_SUMMARIZE_MODELS
        return parse_model_chain(raw, self.gemini_summarize_model, self.gemini_model)

    @property
    def effective_forecast_models(self) -> list[str]:
        from src.backend.adapters.gemini_model_pool import parse_model_chain

        raw = self.gemini_forecast_models.strip() or DEFAULT_FORECAST_MODELS
        return parse_model_chain(
            raw,
            self.gemini_forecast_model or self.gemini_model,
        )

    @property
    def database_file(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
