"""End-to-end AI pipeline integration tests (mocked externals)."""

from unittest.mock import patch

from src.backend.core.database import get_connection, get_latest_forecasts, get_summarized_articles
from src.backend.services.pipeline import run_full_pipeline
from src.backend.services.predictor import run_predictor
from src.backend.services.summarizer import run_summarizer


def test_summarize_and_forecast_e2e(temp_db, sample_article, sample_macro, mock_summary, mock_forecast):
    with patch("src.backend.services.summarizer.GeminiModelPool") as summarize_client:
        summarize_client.return_value.generate_json.return_value = mock_summary
        summarize_client.return_value.last_hit_rate_limit = False
        summarize_client.return_value.last_model_used = "gemini-test"
        summarize_report = run_summarizer()

    assert summarize_report.processed == 1
    articles = get_summarized_articles()
    assert len(articles) == 1
    assert articles[0]["sentiment"] == "bullish"

    with patch("src.backend.services.predictor.GeminiModelPool") as forecast_client:
        forecast_client.return_value.generate_json.return_value = mock_forecast
        predict_report = run_predictor(force=True)

    assert predict_report.horizons_saved == 4
    forecasts = get_latest_forecasts()
    assert len(forecasts) == 4
    horizons = {row["horizon"] for row in forecasts}
    assert horizons == {"day", "week", "month", "quarter"}


def test_full_pipeline_skip_scrape_e2e(
    temp_db,
    sample_article,
    sample_macro,
    mock_summary,
    mock_forecast,
):
    with (
        patch("src.backend.services.summarizer.GeminiModelPool") as summarize_client,
        patch("src.backend.services.predictor.GeminiModelPool") as forecast_client,
    ):
        summarize_client.return_value.generate_json.return_value = mock_summary
        summarize_client.return_value.last_hit_rate_limit = False
        summarize_client.return_value.last_model_used = "gemini-test"
        forecast_client.return_value.generate_json.return_value = mock_forecast

        import asyncio

        report = asyncio.run(run_full_pipeline(skip_scrape=True))

    assert report.summarize is not None
    assert report.summarize.processed == 1
    assert report.predict is not None
    assert report.predict.horizons_saved == 4
    assert report.errors == []

    with get_connection() as conn:
        article_row = conn.execute(
            "SELECT summary, sentiment FROM articles WHERE url = ?",
            ("https://example.com/gold-rally",),
        ).fetchone()
        forecast_count = conn.execute("SELECT COUNT(*) AS c FROM forecasts").fetchone()["c"]

    assert article_row["summary"] is not None
    assert forecast_count == 4


def test_forecast_cache_skip_without_new_data(temp_db, sample_article, sample_macro, mock_summary, mock_forecast):
    with patch("src.backend.services.summarizer.GeminiModelPool") as summarize_client:
        summarize_client.return_value.generate_json.return_value = mock_summary
        summarize_client.return_value.last_hit_rate_limit = False
        summarize_client.return_value.last_model_used = "gemini-test"
        run_summarizer()

    with patch("src.backend.services.predictor.GeminiModelPool") as forecast_client:
        forecast_client.return_value.generate_json.return_value = mock_forecast
        first = run_predictor(force=True)
        second = run_predictor()

    assert first.horizons_saved == 4
    assert second.skipped_cached is True
