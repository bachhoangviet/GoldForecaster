"""Macro data API routes."""

from fastapi import APIRouter, Query

from src.backend.api.schemas import (
    MacroHistoryPoint,
    MacroHistoryResponse,
    MacroLatestResponse,
)
from src.backend.core.database import get_latest_macro, get_macro_history

router = APIRouter(prefix="/api/macro", tags=["macro"])


@router.get("/latest", response_model=MacroLatestResponse)
def macro_latest() -> MacroLatestResponse:
    row = get_latest_macro()
    if not row:
        return MacroLatestResponse()
    return MacroLatestResponse(
        gold_spot=row.get("gold_spot"),
        dxy=row.get("dxy"),
        us10y=row.get("us10y"),
        spdr_holdings=row.get("spdr_holdings"),
        recorded_at=str(row.get("recorded_at")) if row.get("recorded_at") else None,
    )


@router.get("/history", response_model=MacroHistoryResponse)
def macro_history(days: int = Query(default=30, ge=1, le=365)) -> MacroHistoryResponse:
    rows = get_macro_history(days)
    points = [
        MacroHistoryPoint(
            recorded_at=str(row["recorded_at"]),
            gold_spot=float(row["gold_spot"]),
            dxy=float(row["dxy"]) if row.get("dxy") is not None else None,
            us10y=float(row["us10y"]) if row.get("us10y") is not None else None,
        )
        for row in rows
    ]
    return MacroHistoryResponse(days=days, points=points)
