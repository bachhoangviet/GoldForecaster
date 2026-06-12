"""Gemini-powered news summarization service."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from src.backend.adapters.gemini_client import (
    GeminiClient,
    GeminiClientError,
    GeminiRateLimitError,
)
from src.backend.adapters.scraper_utils import truncate_text
from src.backend.core.ai_models import ArticleSummaryResult
from src.backend.core.config import get_settings
from src.backend.core.database import (
    get_connection,
    get_unsummarized_articles,
    get_unsummarized_count,
    update_article_summary,
)
from src.backend.core.prompts import SUMMARIZE_SYSTEM_V1, SUMMARIZE_USER_V1

logger = logging.getLogger(__name__)


@dataclass
class SummarizeReport:
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    batch_size: int = 0
    remaining: int = 0


def run_summarizer(limit: int | None = None) -> SummarizeReport:
    """Summarize articles missing summary using Gemini Flash."""
    settings = get_settings()
    batch_limit = limit or settings.summarize_batch_limit
    articles = get_unsummarized_articles(batch_limit)

    if not articles:
        logger.info("Summarize: no pending articles")
        return SummarizeReport(skipped=0)

    total_in_batch = len(articles)
    logger.info(
        "Summarize: processing %d article(s) (~%.0fs API delay between each)",
        total_in_batch,
        settings.gemini_request_delay_seconds,
    )

    client = GeminiClient()
    report = SummarizeReport(batch_size=total_in_batch)

    for index, article in enumerate(articles):
        article_id = int(article["id"])
        title = str(article["title"])
        source = str(article["source"])
        body = truncate_text(str(article["body"]))

        logger.info(
            "Summarize [%d/%d] %s — %s",
            index + 1,
            total_in_batch,
            source,
            title[:70],
        )

        prompt = SUMMARIZE_USER_V1.format(title=title, source=source, body=body)

        result: ArticleSummaryResult | None = None
        article_retries = 3
        for attempt in range(1, article_retries + 1):
            try:
                result = client.generate_json(
                    prompt=prompt,
                    schema_model=ArticleSummaryResult,
                    system_instruction=SUMMARIZE_SYSTEM_V1,
                )
                break
            except GeminiRateLimitError:
                if attempt >= article_retries:
                    logger.warning(
                        "Rate limit persists — skip article [%d/%d]: %s",
                        index + 1,
                        total_in_batch,
                        title[:50],
                    )
                    report.failed += 1
                    result = None
                    break
                wait = min(120, 40 * attempt)
                logger.warning(
                    "Rate limit 429 — pause %ds then retry article (%d/%d)",
                    wait,
                    attempt,
                    article_retries,
                )
                time.sleep(wait)
            except GeminiClientError as exc:
                logger.warning("Summarize failed for article %d: %s", article_id, exc)
                report.failed += 1
                result = None
                break

        if result is None:
            if index < len(articles) - 1:
                time.sleep(settings.gemini_request_delay_seconds)
            continue

        with get_connection() as conn:
            update_article_summary(
                conn,
                article_id=article_id,
                summary=result.summary.strip(),
                sentiment=result.sentiment,
            )
        report.processed += 1

        if index < len(articles) - 1:
            time.sleep(settings.gemini_request_delay_seconds)

    report.remaining = get_unsummarized_count()
    if report.remaining:
        logger.info(
            "Summarize batch done (%d ok, %d failed). More articles remain — run again.",
            report.processed,
            report.failed,
        )
    else:
        logger.info(
            "Summarize complete (%d ok, %d failed).",
            report.processed,
            report.failed,
        )

    return report
