"""APScheduler jobs for periodic news, macro, and daily report delivery."""

from __future__ import annotations

import asyncio
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.backend.core.config import get_settings
from src.backend.services.daily_job import run_daily_job
from src.backend.services.ingestion import run_full_ingestion, run_macro_pipeline

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


def _news_job() -> None:
    logger.info("Starting scheduled news+macro ingestion")
    report = _run_async(run_full_ingestion())
    logger.info(
        "Ingestion done: inserted=%s skipped=%s macro=%s success=%s failed=%s",
        report.articles_inserted,
        report.articles_skipped,
        report.macro_saved,
        report.sources_succeeded,
        report.sources_failed,
    )


def _macro_job() -> None:
    logger.info("Starting scheduled macro ingestion")
    report = _run_async(run_macro_pipeline())
    logger.info("Macro ingestion done: saved=%s", report.macro_saved)


def _daily_report_job() -> None:
    logger.info("Starting scheduled daily report job")
    report = run_daily_job()
    if report.errors:
        for error in report.errors:
            logger.warning("Daily job: %s", error)
    else:
        logger.info("Daily job completed successfully")


def start_scheduler() -> None:
    """Blocking scheduler: news 4x/day, macro hourly, daily report once per day."""
    settings = get_settings()
    tz = ZoneInfo(settings.daily_job_timezone)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        _news_job,
        CronTrigger(hour="0,6,12,18", minute=0),
        id="news-ingestion",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _macro_job,
        CronTrigger(minute=0),
        id="macro-ingestion",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _daily_report_job,
        CronTrigger(
            hour=settings.daily_job_hour,
            minute=settings.daily_job_minute,
            timezone=tz,
        ),
        id="daily-report",
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "Scheduler started (news: 0/6/12/18 UTC, macro: hourly, daily: %02d:%02d %s)",
        settings.daily_job_hour,
        settings.daily_job_minute,
        settings.daily_job_timezone,
    )
    scheduler.start()
