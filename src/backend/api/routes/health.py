"""Health check routes."""

from fastapi import APIRouter

from src.backend.core.database import get_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    with get_connection() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "ok"}
