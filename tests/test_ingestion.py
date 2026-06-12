"""Integration tests for ingestion persistence and dedupe."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.core.models import MacroSnapshot, RawArticle, ScrapeRunRecord, ScrapeStatus
from src.backend.services.ingestion import run_full_ingestion


def test_ingestion_dedupes_articles(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "ingestion-test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    from src.backend.core.config import get_settings

    get_settings.cache_clear()

    article = RawArticle(
        source="kitco",
        url="https://www.kitco.com/news/test-article",
        title="Test headline for dedupe",
        body="Body",
    )
    run_record = ScrapeRunRecord(
        source="kitco",
        status=ScrapeStatus.SUCCESS,
        article_count=1,
        duration_ms=10,
    )
    macro_record = ScrapeRunRecord(
        source="macro",
        status=ScrapeStatus.SUCCESS,
        duration_ms=20,
    )
    snapshot = MacroSnapshot(
        dxy=120.0,
        us10y=4.3,
        spdr_holdings=900.0,
        gold_spot=2300.0,
    )

    mock_scraper = MagicMock()
    mock_scraper.source = "kitco"

    with (
        patch(
            "src.backend.services.ingestion.get_news_scrapers",
            return_value=[mock_scraper],
        ),
        patch(
            "src.backend.services.ingestion.run_news_scraper",
            new=AsyncMock(return_value=(run_record, [article])),
        ),
        patch(
            "src.backend.services.ingestion.run_macro_ingestion",
            new=AsyncMock(return_value=(macro_record, snapshot)),
        ),
    ):
        first = asyncio.run(run_full_ingestion())
        second = asyncio.run(run_full_ingestion())

    get_settings.cache_clear()

    assert first.articles_inserted == 1
    assert first.articles_skipped == 0
    assert first.macro_saved is True
    assert second.articles_inserted == 0
    assert second.articles_skipped == 1
