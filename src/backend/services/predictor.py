"""Gemini-powered multi-horizon gold trend forecasting."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from src.backend.adapters.gemini_client import GeminiClientError, GeminiRateLimitError
from src.backend.adapters.gemini_model_pool import GeminiModelPool
from src.backend.core.ai_models import ForecastResult
from src.backend.core.config import get_settings
from src.backend.core.database import (
    get_connection,
    get_gold_price_history,
    get_latest_macro,
    get_recent_summarized_articles,
    has_new_data_since_last_forecast,
    insert_forecasts,
)
from src.backend.core.prompts import FORECAST_SYSTEM_V1, FORECAST_USER_V1


@dataclass
class PredictReport:
    skipped_cached: bool = False
    horizons_saved: int = 0
    message: str = ""


def _format_gold_trend(history: list[dict[str, object]]) -> str:
    if not history:
        return "No gold price history available."

    lines: list[str] = []
    previous: float | None = None
    for row in reversed(history):
        price = row.get("gold_spot")
        recorded_at = row.get("recorded_at")
        if price is None:
            continue
        current = float(price)
        if previous is None:
            direction = "baseline"
        elif current > previous:
            direction = "up"
        elif current < previous:
            direction = "down"
        else:
            direction = "flat"
        lines.append(f"- {recorded_at}: {current:.2f} ({direction})")
        previous = current

    return "\n".join(lines) if lines else "No gold price history available."


def _format_news_block(articles: list[dict[str, object]]) -> str:
    if not articles:
        return "No summarized news available."

    chunks: list[str] = []
    for article in articles:
        chunks.append(
            "\n".join(
                [
                    f"[{article.get('sentiment', 'neutral').upper()}] "
                    f"{article.get('source')}: {article.get('title')}",
                    str(article.get("summary") or ""),
                ]
            )
        )
    return "\n\n".join(chunks)


def _sentiment_counts(articles: list[dict[str, object]]) -> tuple[int, int, int]:
    bullish = bearish = neutral = 0
    for article in articles:
        sentiment = str(article.get("sentiment") or "neutral")
        if sentiment == "bullish":
            bullish += 1
        elif sentiment == "bearish":
            bearish += 1
        else:
            neutral += 1
    return bullish, bearish, neutral


def build_forecast_prompt() -> str:
    settings = get_settings()
    macro = get_latest_macro() or {}
    articles = get_recent_summarized_articles(settings.forecast_news_limit)
    bullish, bearish, neutral = _sentiment_counts(articles)
    gold_trend = _format_gold_trend(get_gold_price_history(limit=7))

    return FORECAST_USER_V1.format(
        gold_spot=macro.get("gold_spot", "N/A"),
        dxy=macro.get("dxy", "N/A"),
        us10y=macro.get("us10y", "N/A"),
        spdr_holdings=macro.get("spdr_holdings", "N/A"),
        macro_recorded_at=macro.get("recorded_at", "N/A"),
        gold_trend=gold_trend,
        news_block=_format_news_block(articles),
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
    )


def run_predictor(*, force: bool = False, new_summaries: int = 0) -> PredictReport:
    """Generate 4-horizon forecast when new data is available."""
    if not force and new_summaries == 0 and not has_new_data_since_last_forecast():
        return PredictReport(
            skipped_cached=True,
            message="Forecast skipped — no new articles or macro since last run.",
        )

    articles = get_recent_summarized_articles(1)
    if not articles:
        return PredictReport(
            skipped_cached=True,
            message="Forecast skipped — no summarized articles available.",
        )

    settings = get_settings()
    model_chain = settings.effective_forecast_models
    logger.info(
        "Forecast: model chain (%s) for 4-horizon trend analysis...",
        " → ".join(model_chain),
    )
    pool = GeminiModelPool(
        model_chain,
        cooldown_seconds=settings.gemini_model_cooldown_seconds,
    )
    prompt = build_forecast_prompt()
    try:
        result = pool.generate_json(
            prompt=prompt,
            schema_model=ForecastResult,
            system_instruction=FORECAST_SYSTEM_V1,
            temperature=0.1,
        )
    except (GeminiRateLimitError, GeminiClientError) as exc:
        return PredictReport(message=f"Forecast failed: {exc}")

    with get_connection() as conn:
        insert_forecasts(
            conn,
            day_trend=result.day.trend,
            day_confidence=result.day.confidence,
            day_reasoning=result.day.reasoning,
            week_trend=result.week.trend,
            week_confidence=result.week.confidence,
            week_reasoning=result.week.reasoning,
            month_trend=result.month.trend,
            month_confidence=result.month.confidence,
            month_reasoning=result.month.reasoning,
            quarter_trend=result.quarter.trend,
            quarter_confidence=result.quarter.confidence,
            quarter_reasoning=result.quarter.reasoning,
        )

    return PredictReport(
        horizons_saved=4,
        message="Forecast saved for day/week/month/quarter horizons.",
    )
