"""Generate detailed daily Vietnamese gold report from today's summaries."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from src.backend.adapters.gemini_client import GeminiClientError, GeminiRateLimitError
from src.backend.adapters.gemini_model_pool import GeminiModelPool
from src.backend.core.ai_models import DailyGoldReport
from src.backend.core.config import get_settings
from src.backend.core.database import (
    get_connection,
    get_gold_price_history,
    get_latest_daily_report,
    get_latest_macro,
    get_recent_summarized_articles,
    insert_daily_report,
    insert_forecasts,
)
from src.backend.core.prompts import DAILY_REPORT_SYSTEM_V1, DAILY_REPORT_USER_V1
from src.backend.services.predictor import (
    _format_gold_trend,
    _format_news_block,
    _sentiment_counts,
)

logger = logging.getLogger(__name__)


@dataclass
class DailyReportResult:
    saved: bool = False
    title: str = ""
    message: str = ""


def _build_daily_report_prompt() -> str:
    settings = get_settings()
    macro = get_latest_macro() or {}
    articles = get_recent_summarized_articles(settings.forecast_news_limit)
    bullish, bearish, neutral = _sentiment_counts(articles)

    return DAILY_REPORT_USER_V1.format(
        gold_spot=macro.get("gold_spot", "N/A"),
        dxy=macro.get("dxy", "N/A"),
        us10y=macro.get("us10y", "N/A"),
        spdr_holdings=macro.get("spdr_holdings", "N/A"),
        macro_recorded_at=macro.get("recorded_at", "N/A"),
        gold_trend=_format_gold_trend(get_gold_price_history(limit=7)),
        news_block=_format_news_block(articles),
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
    )


def run_daily_report() -> DailyReportResult:
    """Build and persist a detailed Vietnamese daily gold report."""
    prompt = _build_daily_report_prompt()
    if "No summarized news available" in prompt:
        return DailyReportResult(
            message="Báo cáo bỏ qua — chưa có tin tóm tắt trong ngày.",
        )

    settings = get_settings()
    model_chain = settings.effective_forecast_models
    logger.info("Daily report: model chain (%s)", " → ".join(model_chain))
    pool = GeminiModelPool(
        model_chain,
        cooldown_seconds=settings.gemini_model_cooldown_seconds,
    )

    try:
        report = pool.generate_json(
            prompt=prompt,
            schema_model=DailyGoldReport,
            system_instruction=DAILY_REPORT_SYSTEM_V1,
            temperature=0.15,
        )
    except (GeminiRateLimitError, GeminiClientError) as exc:
        return DailyReportResult(message=f"Báo cáo thất bại: {exc}")

    forecast = report.to_forecast_result()
    report_json = report.model_dump_json(ensure_ascii=False)

    with get_connection() as conn:
        insert_daily_report(conn, title=report.title, report_json=report_json)
        insert_forecasts(
            conn,
            day_trend=forecast.day.trend,
            day_confidence=forecast.day.confidence,
            day_reasoning=forecast.day.reasoning,
            week_trend=forecast.week.trend,
            week_confidence=forecast.week.confidence,
            week_reasoning=forecast.week.reasoning,
            month_trend=forecast.month.trend,
            month_confidence=forecast.month.confidence,
            month_reasoning=forecast.month.reasoning,
            quarter_trend=forecast.quarter.trend,
            quarter_confidence=forecast.quarter.confidence,
            quarter_reasoning=forecast.quarter.reasoning,
        )

    logger.info("Daily report saved: %s", report.title)
    return DailyReportResult(
        saved=True,
        title=report.title,
        message="Đã lưu báo cáo ngày và cập nhật forecast dashboard.",
    )


def load_latest_daily_report() -> DailyGoldReport | None:
    row = get_latest_daily_report()
    if not row:
        return None
    return DailyGoldReport.model_validate(json.loads(str(row["report_json"])))


def _report_is_from_today(row: dict[str, object]) -> bool:
    created_at = str(row.get("created_at") or "")
    if not created_at:
        return False
    with get_connection() as conn:
        match = conn.execute(
            "SELECT 1 WHERE date(?) = date('now', 'localtime')",
            (created_at,),
        ).fetchone()
    return bool(match)


def ensure_daily_report(*, force: bool = False) -> DailyReportResult:
    """Generate today's report if missing or stale."""
    if not force:
        row = get_latest_daily_report()
        if row and _report_is_from_today(row):
            report = DailyGoldReport.model_validate(json.loads(str(row["report_json"])))
            return DailyReportResult(
                saved=True,
                title=report.title,
                message="Đã có báo cáo forecast trong ngày.",
            )
    return run_daily_report()
