"""Pydantic models for Gemini structured outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Sentiment = Literal["bullish", "bearish", "neutral"]
Trend = Literal["up", "down", "sideways"]
Horizon = Literal["day", "week", "month", "quarter"]


class ArticleSummaryResult(BaseModel):
    summary: str = Field(
        description="3-5 concise bullet points about gold market impact"
    )
    sentiment: Sentiment


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
