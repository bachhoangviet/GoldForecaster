"""Ingestion orchestrator: parallel scrapers, dedupe, persistence."""

from __future__ import annotations

import asyncio
import logging

from src.backend.adapters.market_api import run_macro_ingestion
from src.backend.adapters.web_scrapers import get_news_scrapers, run_news_scraper
from src.backend.core.database import (
    get_connection,
    insert_article,
    insert_macro_snapshot,
    log_scrape_run,
)
from src.backend.core.models import IngestionReport, RawArticle, ScrapeRunRecord

logger = logging.getLogger(__name__)


def _log_scrape_result(record: ScrapeRunRecord, article_count: int = 0) -> None:
    logger.info(
        "[%s] %s duration=%sms articles=%s error=%s",
        record.source,
        record.status.value,
        record.duration_ms,
        article_count,
        record.error or "-",
    )


def _persist_articles(articles: list[RawArticle]) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    with get_connection() as conn:
        for article in articles:
            saved = insert_article(
                conn,
                source=article.source,
                url=article.url,
                url_hash=article.url_hash,
                title=article.title,
                body=article.body,
                published_at=article.published_at,
            )
            if saved:
                inserted += 1
            else:
                skipped += 1
    return inserted, skipped


def _persist_scrape_run(record: ScrapeRunRecord) -> None:
    with get_connection() as conn:
        log_scrape_run(
            conn,
            source=record.source,
            status=record.status.value,
            error=record.error,
            duration_ms=record.duration_ms,
        )


async def run_news_ingestion(source: str | None = None) -> IngestionReport:
    scrapers = get_news_scrapers(source)
    report = IngestionReport()

    results = await asyncio.gather(
        *(run_news_scraper(scraper) for scraper in scrapers),
        return_exceptions=False,
    )

    for record, articles in results:
        report.scrape_runs.append(record)
        _persist_scrape_run(record)
        _log_scrape_result(record, article_count=len(articles))
        if articles:
            inserted, skipped = _persist_articles(articles)
            report.articles_inserted += inserted
            report.articles_skipped += skipped

    return report


async def run_macro_pipeline() -> IngestionReport:
    report = IngestionReport()
    record, snapshot = await run_macro_ingestion()
    report.scrape_runs.append(record)
    _persist_scrape_run(record)
    _log_scrape_result(record)

    if snapshot is not None:
        with get_connection() as conn:
            insert_macro_snapshot(
                conn,
                dxy=snapshot.dxy,
                us10y=snapshot.us10y,
                spdr_holdings=snapshot.spdr_holdings,
                gold_spot=snapshot.gold_spot,
            )
        report.macro_saved = True

    return report


async def run_full_ingestion(
    *,
    source: str | None = None,
    news_only: bool = False,
    macro_only: bool = False,
) -> IngestionReport:
    if news_only and macro_only:
        raise ValueError("Choose only one of news_only or macro_only.")

    if macro_only:
        return await run_macro_pipeline()

    news_report = await run_news_ingestion(source=source)
    if news_only:
        return news_report

    macro_report = await run_macro_pipeline()
    return IngestionReport(
        articles_inserted=news_report.articles_inserted,
        articles_skipped=news_report.articles_skipped,
        macro_saved=macro_report.macro_saved,
        scrape_runs=news_report.scrape_runs + macro_report.scrape_runs,
    )
