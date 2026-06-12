"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routes.forecasts import router as forecasts_router
from src.backend.api.routes.health import router as health_router
from src.backend.api.routes.macro import router as macro_router
from src.backend.api.routes.news import router as news_router
from src.backend.core.config import get_settings
from src.backend.core.database import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()

    app = FastAPI(
        title="GoldForecaster API",
        description="Backend API for gold macro data, news, and AI forecasts.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(macro_router)
    app.include_router(news_router)
    app.include_router(forecasts_router)
    return app


app = create_app()
