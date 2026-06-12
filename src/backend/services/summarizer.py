"""Gemini-powered news summarization service."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from src.backend.adapters.gemini_client import GeminiClientError, GeminiRateLimitError
from src.backend.adapters.gemini_model_pool import GeminiModelPool
from src.backend.adapters.scraper_utils import truncate_text
from src.backend.core.ai_models import ArticleSummaryResult
from src.backend.core.article_quality import SKIPPED_SUMMARY_PREFIX, junk_article_reason
from src.backend.core.config import get_settings
from src.backend.core.database import (
    delete_articles_before_today,
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
    cleared_stale: int = 0
    batch_size: int = 0
    remaining: int = 0


def _mark_skipped_article(*, article_id: int, reason: str) -> None:
    with get_connection() as conn:
        update_article_summary(
            conn,
            article_id=article_id,
            summary=f"{SKIPPED_SUMMARY_PREFIX} {reason}",
            sentiment="neutral",
        )


def _inter_article_delay(*, settings, had_rate_limit: bool) -> float:
    delay = settings.gemini_request_delay_seconds
    if had_rate_limit:
        delay += settings.gemini_rate_limit_cooldown_seconds
        logger.info(
            "Rate limit recovery — extra cooldown %.0fs before next article",
            settings.gemini_rate_limit_cooldown_seconds,
        )
    return delay


def run_summarizer(
    limit: int | None = None,
    *,
    clear_stale: bool | None = None,
) -> SummarizeReport:
    """Summarize articles missing summary using Gemini Flash."""
    settings = get_settings()
    should_clear_stale = (
        settings.clear_stale_articles_on_summarize
        if clear_stale is None
        else clear_stale
    )
    cleared_stale = 0
    if should_clear_stale:
        cleared_stale = delete_articles_before_today()
        if cleared_stale:
            logger.info(
                "Summarize: cleared %d article(s) from previous days",
                cleared_stale,
            )

    batch_limit = limit or settings.summarize_batch_limit
    articles = get_unsummarized_articles(batch_limit)

    if not articles:
        logger.info("Summarize: no pending articles")
        return SummarizeReport(skipped=0)

    model_chain = settings.effective_summarize_models
    total_in_batch = len(articles)
    logger.info(
        "Summarize: processing %d article(s) via model chain (%s) (~%.0fs delay)",
        total_in_batch,
        " → ".join(model_chain),
        settings.gemini_request_delay_seconds,
    )

    pool: GeminiModelPool | None = None
    report = SummarizeReport(batch_size=total_in_batch, cleared_stale=cleared_stale)

    for index, article in enumerate(articles):
        article_id = int(article["id"])
        title = str(article["title"])
        source = str(article["source"])
        body = truncate_text(str(article["body"]))

        skip_reason = junk_article_reason(title=title, body=body, source=source)
        if skip_reason:
            logger.info(
                "Summarize [%d/%d] skip %s — %s (%s)",
                index + 1,
                total_in_batch,
                source,
                title[:50],
                skip_reason,
            )
            _mark_skipped_article(article_id=article_id, reason=skip_reason)
            report.skipped += 1
            continue

        logger.info(
            "Summarize [%d/%d] %s — %s",
            index + 1,
            total_in_batch,
            source,
            title[:70],
        )

        if pool is None:
            pool = GeminiModelPool(
                model_chain,
                cooldown_seconds=settings.gemini_model_cooldown_seconds,
            )

        prompt = SUMMARIZE_USER_V1.format(title=title, source=source, body=body)

        result: ArticleSummaryResult | None = None
        had_rate_limit = False
        try:
            result = pool.generate_json(
                prompt=prompt,
                schema_model=ArticleSummaryResult,
                system_instruction=SUMMARIZE_SYSTEM_V1,
            )
            had_rate_limit = pool.last_hit_rate_limit
            if pool.last_model_used != model_chain[0]:
                logger.info(
                    "Summarize [%d/%d] succeeded with fallback model %s",
                    index + 1,
                    total_in_batch,
                    pool.last_model_used,
                )
        except GeminiRateLimitError:
            logger.warning(
                "Rate limit on all models — skip article [%d/%d]: %s",
                index + 1,
                total_in_batch,
                title[:50],
            )
            report.failed += 1
            had_rate_limit = True
        except GeminiClientError as exc:
            logger.warning("Summarize failed for article %d: %s", article_id, exc)
            report.failed += 1

        if result is None:
            if index < len(articles) - 1:
                time.sleep(_inter_article_delay(settings=settings, had_rate_limit=had_rate_limit))
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
            time.sleep(_inter_article_delay(settings=settings, had_rate_limit=had_rate_limit))

    report.remaining = get_unsummarized_count()
    if report.remaining:
        logger.info(
            "Summarize batch done (%d ok, %d skipped, %d failed). More articles remain — run again.",
            report.processed,
            report.skipped,
            report.failed,
        )
    else:
        logger.info(
            "Summarize complete (%d ok, %d skipped, %d failed).",
            report.processed,
            report.skipped,
            report.failed,
        )

    return report
