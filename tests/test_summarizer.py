"""Tests for summarizer service."""

from unittest.mock import MagicMock, patch

from src.backend.core.ai_models import ArticleSummaryResult
from src.backend.services.summarizer import run_summarizer


def test_run_summarizer_updates_articles(tmp_path, monkeypatch):
    db_file = tmp_path / "summarizer.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.backend.core.config import get_settings
    from src.backend.core.database import get_connection, insert_article

    get_settings.cache_clear()

    with get_connection() as conn:
        insert_article(
            conn,
            source="kitco",
            url="https://example.com/a1",
            url_hash="hash1",
            title="Gold rises on weak dollar",
            body="Gold prices moved higher as the dollar weakened.",
            published_at=None,
        )

    mock_result = ArticleSummaryResult(
        summary="- Dollar weakness supports gold\n- Risk sentiment improved",
        sentiment="bullish",
    )

    with patch("src.backend.services.summarizer.GeminiClient") as mock_client_cls:
        mock_client_cls.return_value.generate_json.return_value = mock_result
        report = run_summarizer(limit=5)

    get_settings.cache_clear()

    assert report.processed == 1
    assert report.failed == 0

    with get_connection() as conn:
        row = conn.execute(
            "SELECT summary, sentiment FROM articles WHERE url = ?",
            ("https://example.com/a1",),
        ).fetchone()

    assert row["sentiment"] == "bullish"
    assert "Dollar weakness" in row["summary"]


def test_run_summarizer_no_pending_articles(tmp_path, monkeypatch):
    db_file = tmp_path / "summarizer-empty.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    with patch("src.backend.services.summarizer.GeminiClient") as mock_client_cls:
        report = run_summarizer()

    get_settings.cache_clear()
    mock_client_cls.assert_not_called()
    assert report.processed == 0
