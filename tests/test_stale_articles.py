"""Tests for daily article cleanup before summarize."""

from datetime import datetime
from unittest.mock import patch

from src.backend.core.database import (
    delete_articles_before_today,
    get_connection,
    get_summarized_articles,
    get_unsummarized_count,
    insert_article,
)
from src.backend.services.summarizer import run_summarizer


def _insert_article_with_scraped_at(
    conn,
    *,
    url: str,
    url_hash: str,
    scraped_at: str,
) -> None:
    insert_article(
        conn,
        source="kitco",
        url=url,
        url_hash=url_hash,
        title="Gold market update",
        body="Gold prices moved higher as the dollar weakened across major pairs.",
        published_at=None,
    )
    conn.execute(
        "UPDATE articles SET scraped_at = ? WHERE url = ?",
        (scraped_at, url),
    )


def test_delete_articles_before_today_removes_old_rows(tmp_path, monkeypatch):
    db_file = tmp_path / "stale.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    with get_connection() as conn:
        _insert_article_with_scraped_at(
            conn,
            url="https://example.com/old",
            url_hash="old-hash",
            scraped_at="2020-01-01 10:00:00",
        )
        _insert_article_with_scraped_at(
            conn,
            url="https://example.com/today",
            url_hash="today-hash",
            scraped_at=datetime.now().strftime("%Y-%m-%d 10:00:00"),
        )
        conn.commit()

    removed = delete_articles_before_today()
    get_settings.cache_clear()

    assert removed == 1

    with get_connection() as conn:
        rows = conn.execute("SELECT url FROM articles").fetchall()

    assert [row["url"] for row in rows] == ["https://example.com/today"]


def test_run_summarizer_clears_stale_by_default(tmp_path, monkeypatch):
    db_file = tmp_path / "summarizer-stale.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CLEAR_STALE_ARTICLES_ON_SUMMARIZE", "true")

    from src.backend.core.ai_models import ArticleSummaryResult
    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    with get_connection() as conn:
        _insert_article_with_scraped_at(
            conn,
            url="https://example.com/old",
            url_hash="old-hash",
            scraped_at="2020-01-01 10:00:00",
        )
        _insert_article_with_scraped_at(
            conn,
            url="https://example.com/today",
            url_hash="today-hash",
            scraped_at=datetime.now().strftime("%Y-%m-%d 10:00:00"),
        )
        conn.commit()

    mock_result = ArticleSummaryResult(
        summary="- Dollar weakness supports gold",
        sentiment="bullish",
    )

    with patch("src.backend.services.summarizer.GeminiModelPool") as mock_pool_cls:
        mock_pool_cls.return_value.generate_json.return_value = mock_result
        mock_pool_cls.return_value.last_hit_rate_limit = False
        mock_pool_cls.return_value.last_model_used = "gemini-test"
        report = run_summarizer(limit=5)

    get_settings.cache_clear()

    assert report.cleared_stale == 1
    assert report.processed == 1
    assert get_unsummarized_count() == 0
    assert len(get_summarized_articles()) == 1
