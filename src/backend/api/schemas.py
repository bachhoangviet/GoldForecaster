"""Pydantic response models for public API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["bullish", "bearish", "neutral"]
Trend = Literal["up", "down", "sideways"]
Horizon = Literal["day", "week", "month", "quarter"]


class MacroLatestResponse(BaseModel):
    gold_spot: float | None = None
    dxy: float | None = None
    us10y: float | None = None
    spdr_holdings: float | None = None
    recorded_at: str | None = None


class MacroHistoryPoint(BaseModel):
    recorded_at: str
    gold_spot: float
    dxy: float | None = None
    us10y: float | None = None


class MacroHistoryResponse(BaseModel):
    days: int
    points: list[MacroHistoryPoint]


class NewsArticleResponse(BaseModel):
    id: int
    source: str
    title: str
    summary: str
    sentiment: Sentiment
    scraped_at: str
    published_at: str | None = None


class NewsListResponse(BaseModel):
    count: int
    articles: list[NewsArticleResponse]


class ForecastHorizonResponse(BaseModel):
    horizon: Horizon
    trend: Trend
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    created_at: str


class ForecastLatestResponse(BaseModel):
    created_at: str | None = None
    horizons: list[ForecastHorizonResponse]
