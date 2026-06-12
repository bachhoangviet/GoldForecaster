"""Pydantic models for Gemini structured outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Sentiment = Literal["bullish", "bearish", "neutral"]
Trend = Literal["up", "down", "sideways"]
Horizon = Literal["day", "week", "month", "quarter"]


class ArticleSummaryResult(BaseModel):
    summary: str = Field(
        description=(
            "Single string with 3-5 bullet lines about gold market impact; "
            "each line prefixed with '- '"
        )
    )
    sentiment: Sentiment

    @field_validator("summary", mode="before")
    @classmethod
    def coerce_summary_to_string(cls, value: object) -> object:
        if isinstance(value, list):
            lines: list[str] = []
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    continue
                text = item.strip()
                lines.append(text if text.startswith("-") else f"- {text}")
            return "\n".join(lines)
        return value


class HorizonForecast(BaseModel):
    trend: Trend
    confidence: int = Field(ge=0, le=100)
    reasoning: str = Field(max_length=500)

    @field_validator("reasoning")
    @classmethod
    def forbid_price_targets(cls, value: str) -> str:
        lowered = value.lower()
        banned = ("$", "usd/oz", "price target", "will reach", "predicted price")
        if any(token in lowered for token in banned):
            raise ValueError("Reasoning must not include explicit price targets")
        return value


class ForecastResult(BaseModel):
    day: HorizonForecast
    week: HorizonForecast
    month: HorizonForecast
    quarter: HorizonForecast

    def iter_horizons(self) -> list[tuple[Horizon, HorizonForecast]]:
        return [
            ("day", self.day),
            ("week", self.week),
            ("month", self.month),
            ("quarter", self.quarter),
        ]


class ReportHorizonForecast(BaseModel):
    """Horizon block for the daily Vietnamese report (no USD price-target ban)."""

    trend: Trend
    confidence: int = Field(ge=0, le=100)
    reasoning: str = Field(max_length=800)


class DailyGoldReport(BaseModel):
    """Detailed daily gold outlook for international and Vietnam markets."""

    title: str = Field(max_length=200)
    executive_summary: str = Field(max_length=2000)
    news_rationale: str = Field(
        max_length=3000,
        description="Giải thích dự báo dựa trên tin tóm tắt trong ngày (trích nguồn).",
    )
    international_analysis: str = Field(max_length=3000)
    domestic_analysis: str = Field(max_length=3000)
    international_trend: Trend
    domestic_trend: Trend
    international_price_outlook: str = Field(max_length=1000)
    domestic_price_outlook: str = Field(max_length=1000)
    confidence: int = Field(ge=0, le=100)
    key_drivers: list[str] = Field(max_length=6)
    risks: list[str] = Field(max_length=5)
    day: ReportHorizonForecast
    week: ReportHorizonForecast
    month: ReportHorizonForecast
    quarter: ReportHorizonForecast

    def to_forecast_result(self) -> ForecastResult:
        """Map report horizons to dashboard forecast rows."""

        def _map(h: ReportHorizonForecast) -> HorizonForecast:
            reasoning = h.reasoning[:500].replace("$", "")
            return HorizonForecast(
                trend=h.trend,
                confidence=h.confidence,
                reasoning=reasoning,
            )

        return ForecastResult(
            day=_map(self.day),
            week=_map(self.week),
            month=_map(self.month),
            quarter=_map(self.quarter),
        )
