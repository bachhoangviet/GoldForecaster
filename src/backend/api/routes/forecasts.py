"""Forecast API routes."""

from fastapi import APIRouter

from src.backend.api.schemas import ForecastHorizonResponse, ForecastLatestResponse
from src.backend.core.database import get_latest_forecasts

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get("/latest", response_model=ForecastLatestResponse)
def forecasts_latest() -> ForecastLatestResponse:
    rows = get_latest_forecasts()
    if not rows:
        return ForecastLatestResponse(created_at=None, horizons=[])

    horizons = [
        ForecastHorizonResponse(
            horizon=row["horizon"],  # type: ignore[arg-type]
            trend=row["trend"],  # type: ignore[arg-type]
            confidence=int(row["confidence"]),
            reasoning=str(row["reasoning"]),
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]
    return ForecastLatestResponse(
        created_at=str(rows[0]["created_at"]),
        horizons=horizons,
    )
