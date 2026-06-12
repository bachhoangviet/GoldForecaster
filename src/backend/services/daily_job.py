"""Daily pipeline: ingest → summarize → detailed report → Telegram."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from src.backend.core.models import IngestionReport
from src.backend.services.daily_report import DailyReportResult, run_daily_report
from src.backend.services.ingestion import run_full_ingestion
from src.backend.services.summarizer import SummarizeReport, run_summarizer
from src.backend.services.telegram_digest import TelegramDigestResult, send_daily_digest

logger = logging.getLogger(__name__)


@dataclass
class DailyJobReport:
    ingestion: IngestionReport | None = None
    summarize: SummarizeReport | None = None
    daily_report: DailyReportResult | None = None
    telegram: TelegramDigestResult | None = None
    errors: list[str] = field(default_factory=list)


def run_daily_job(*, skip_telegram: bool = False) -> DailyJobReport:
    """Run the full daily GoldForecaster workflow."""
    report = DailyJobReport()
    logger.info("Daily job: starting ingest → summarize → report → telegram")

    try:
        report.ingestion = asyncio.run(run_full_ingestion())
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Ingestion failed: {exc}")
        logger.exception("Daily job ingestion failed")
        return report

    try:
        report.summarize = run_summarizer(clear_stale=True)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Summarize failed: {exc}")
        logger.exception("Daily job summarize failed")
        return report

    try:
        report.daily_report = run_daily_report()
        if not report.daily_report.saved:
            report.errors.append(report.daily_report.message)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Daily report failed: {exc}")
        logger.exception("Daily job report failed")

    if not skip_telegram:
        try:
            report.telegram = send_daily_digest()
            if not report.telegram.sent:
                report.errors.append(report.telegram.message)
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"Telegram failed: {exc}")
            logger.exception("Daily job telegram failed")

    logger.info(
        "Daily job done: summarize=%s report=%s telegram=%s errors=%s",
        report.summarize.processed if report.summarize else 0,
        report.daily_report.saved if report.daily_report else False,
        report.telegram.sent if report.telegram else False,
        len(report.errors),
    )
    return report
