"""End-to-end pipeline: ingest → summarize → forecast."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from src.backend.core.models import IngestionReport
from src.backend.services.ingestion import run_full_ingestion
from src.backend.services.predictor import PredictReport, run_predictor
from src.backend.services.summarizer import SummarizeReport, run_summarizer


@dataclass
class PipelineReport:
    ingestion: IngestionReport | None = None
    summarize: SummarizeReport | None = None
    predict: PredictReport | None = None
    errors: list[str] = field(default_factory=list)


async def run_full_pipeline(
    *,
    source: str | None = None,
    skip_scrape: bool = False,
    news_only: bool = False,
    macro_only: bool = False,
    force_forecast: bool = False,
    summarize_limit: int | None = None,
) -> PipelineReport:
    report = PipelineReport()

    if not skip_scrape:
        try:
            report.ingestion = await run_full_ingestion(
                source=source,
                news_only=news_only,
                macro_only=macro_only,
            )
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"Ingestion failed: {exc}")
            return report

    try:
        report.summarize = run_summarizer(limit=summarize_limit)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Summarize failed: {exc}")
        return report

    try:
        new_summaries = report.summarize.processed if report.summarize else 0
        report.predict = run_predictor(
            force=force_forecast,
            new_summaries=new_summaries,
        )
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Forecast failed: {exc}")

    return report
