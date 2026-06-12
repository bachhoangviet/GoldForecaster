"""Shared pytest fixtures for GoldForecaster tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backend.core.ai_models import ArticleSummaryResult, ForecastResult, HorizonForecast
from src.backend.core.database import get_connection, insert_article, insert_macro_snapshot


@pytest.fixture
def temp_db(monkeypatch, tmp_path: Path):
    """Isolated SQLite database per test."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("FRED_API_KEY", "test-fred-key")

    from src.backend.core.config import get_settings

    get_settings.cache_clear()
    yield db_file
    get_settings.cache_clear()


@pytest.fixture
def sample_article(temp_db: Path) -> dict[str, str]:
    with get_connection() as conn:
        insert_article(
            conn,
            source="kitco",
            url="https://example.com/gold-rally",
            url_hash="hash-gold-rally",
            title="Gold rallies on softer dollar",
            body="Gold prices rose as the US dollar weakened and yields fell.",
            published_at=None,
        )
    return {
        "url": "https://example.com/gold-rally",
        "title": "Gold rallies on softer dollar",
    }


@pytest.fixture
def sample_macro(temp_db: Path) -> None:
    with get_connection() as conn:
        insert_macro_snapshot(
            conn,
            dxy=121.2,
            us10y=4.15,
            spdr_holdings=905.5,
            gold_spot=2340.0,
        )


@pytest.fixture
def mock_summary() -> ArticleSummaryResult:
    return ArticleSummaryResult(
        summary="- Dollar weakness supports gold\n- Lower yields are supportive",
        sentiment="bullish",
    )


@pytest.fixture
def mock_forecast() -> ForecastResult:
    horizon = HorizonForecast(
        trend="up",
        confidence=72,
        reasoning="Weaker USD and supportive macro backdrop favor gold.",
    )
    sideways = HorizonForecast(
        trend="sideways",
        confidence=54,
        reasoning="Mixed macro signals keep gold range-bound.",
    )
    return ForecastResult(day=horizon, week=horizon, month=sideways, quarter=sideways)
