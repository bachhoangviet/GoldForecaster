"""News API routes."""

from typing import Literal

from fastapi import APIRouter, Query

from src.backend.api.schemas import NewsArticleResponse, NewsListResponse
from src.backend.core.database import get_summarized_articles

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
def list_news(
    sentiment: Literal["bullish", "bearish", "neutral"] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> NewsListResponse:
    rows = get_summarized_articles(limit=limit, sentiment=sentiment)
    articles = [
        NewsArticleResponse(
            id=int(row["id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            summary=str(row["summary"] or ""),
            sentiment=row["sentiment"],  # type: ignore[arg-type]
            scraped_at=str(row["scraped_at"]),
            published_at=str(row["published_at"]) if row.get("published_at") else None,
        )
        for row in rows
    ]
    return NewsListResponse(count=len(articles), articles=articles)
