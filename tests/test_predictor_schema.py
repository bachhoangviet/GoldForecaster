"""Tests for predictor schema, cache gate, and persistence."""

from unittest.mock import patch

from src.backend.core.ai_models import ForecastResult, HorizonForecast
from src.backend.core.database import get_connection, insert_article
from src.backend.services.predictor import run_predictor


def _sample_forecast() -> ForecastResult:
    horizon = HorizonForecast(
        trend="up",
        confidence=72,
        reasoning="Weaker USD and lower real yields support gold.",
    )
    sideways = HorizonForecast(
        trend="sideways",
        confidence=55,
        reasoning="Mixed macro signals keep gold range-bound.",
    )
    return ForecastResult(day=horizon, week=horizon, month=sideways, quarter=sideways)


def _seed_article(conn, url: str) -> None:
    insert_article(
        conn,
        source="kitco",
        url=url,
        url_hash=url,
        title="Gold market update",
        body="Gold traded higher on macro uncertainty.",
        published_at=None,
    )
    conn.execute(
        """
        UPDATE articles
        SET summary = '- Macro uncertainty supports gold',
            sentiment = 'bullish'
        WHERE url = ?
        """,
        (url,),
    )


def test_run_predictor_skips_when_cached(tmp_path, monkeypatch):
    db_file = tmp_path / "predictor-cache.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    with get_connection() as conn:
        _seed_article(conn, "https://example.com/cached")
        conn.execute(
            """
            INSERT INTO forecasts (horizon, trend, confidence, reasoning)
            VALUES ('day', 'up', 70, 'Existing forecast')
            """
        )

    with patch("src.backend.services.predictor.GeminiModelPool") as mock_pool_cls:
        report = run_predictor()

    get_settings.cache_clear()
    mock_pool_cls.assert_not_called()
    assert report.skipped_cached is True


def test_run_predictor_force_bypasses_cache(tmp_path, monkeypatch):
    db_file = tmp_path / "predictor-force.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    with get_connection() as conn:
        _seed_article(conn, "https://example.com/force")
        conn.execute(
            """
            INSERT INTO forecasts (horizon, trend, confidence, reasoning)
            VALUES ('day', 'up', 70, 'Existing forecast')
            """
        )

    with patch("src.backend.services.predictor.GeminiModelPool") as mock_pool_cls:
        mock_pool_cls.return_value.generate_json.return_value = _sample_forecast()
        report = run_predictor(force=True)

    get_settings.cache_clear()

    assert report.skipped_cached is False
    assert report.horizons_saved == 4

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM forecasts").fetchone()["c"]

    assert count == 5


def test_horizon_forecast_rejects_price_targets():
    try:
        HorizonForecast(
            trend="up",
            confidence=80,
            reasoning="Gold will reach $3000 next month",
        )
        raised = False
    except ValueError:
        raised = True

    assert raised is True
