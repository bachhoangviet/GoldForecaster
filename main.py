#!/usr/bin/env python3
"""GoldForecaster CLI shell for local development and testing."""

from __future__ import annotations

import asyncio
import sys

import click
import uvicorn

from src.backend.adapters.gemini_client import (
    GeminiAuthError,
    GeminiClient,
    GeminiClientError,
    GeminiNetworkError,
    GeminiRateLimitError,
)
from src.backend.core.config import get_settings
from src.backend.core.logging_config import configure_logging
from src.backend.core.database import (
    get_latest_forecasts,
    get_latest_macro,
    get_table_counts,
    get_unsummarized_count,
    init_db,
)
from src.backend.core.models import ScrapeStatus
from src.backend.services.ingestion import run_full_ingestion
from src.backend.services.pipeline import run_full_pipeline
from src.backend.services.predictor import run_predictor
from src.backend.services.scheduler import start_scheduler
from src.backend.services.summarizer import run_summarizer


@click.group(invoke_without_command=True)
@click.option("--test-ai", is_flag=True, help="Ping Gemini API connectivity.")
@click.option("--run-scraper", is_flag=True, help="Run data ingestion pipeline.")
@click.option("--run-pipeline", is_flag=True, help="Ingest, summarize, and forecast.")
@click.option("--summarize", is_flag=True, help="Summarize unsummarized articles.")
@click.option("--forecast", is_flag=True, help="Generate multi-horizon forecast.")
@click.option("--force-forecast", is_flag=True, help="Bypass forecast cache gate.")
@click.option("--skip-scrape", is_flag=True, help="Skip ingestion in --run-pipeline.")
@click.option(
    "--summarize-limit",
    type=int,
    default=None,
    help="Max articles to summarize per run (default: 20).",
)
@click.option(
    "--source",
    type=click.Choice(["kitco", "fed", "cnbc", "reuters", "bloomberg"]),
    help="Run a single news source (with --run-scraper/--run-pipeline).",
)
@click.option("--news-only", is_flag=True, help="Only ingest news sources.")
@click.option("--macro-only", is_flag=True, help="Only ingest macro data.")
@click.option("--show-data", is_flag=True, help="Show SQLite row counts and latest macro.")
@click.option("--serve", is_flag=True, help="Start FastAPI server.")
@click.option("--worker", is_flag=True, help="Start ingestion scheduler (blocking).")
def cli(
    test_ai: bool,
    run_scraper: bool,
    run_pipeline: bool,
    summarize: bool,
    forecast: bool,
    force_forecast: bool,
    skip_scrape: bool,
    summarize_limit: int | None,
    source: str | None,
    news_only: bool,
    macro_only: bool,
    show_data: bool,
    serve: bool,
    worker: bool,
) -> None:
    """GoldForecaster command-line interface."""
    flags = (
        test_ai,
        run_scraper,
        run_pipeline,
        summarize,
        forecast,
        show_data,
        serve,
        worker,
    )
    if not any(flags):
        click.echo(ctx.get_help() if (ctx := click.get_current_context()) else "")
        return

    init_db()

    if test_ai:
        _run_test_ai()
    if run_scraper:
        _run_scraper(source=source, news_only=news_only, macro_only=macro_only)
    if run_pipeline:
        _run_pipeline(
            source=source,
            skip_scrape=skip_scrape,
            news_only=news_only,
            macro_only=macro_only,
            force_forecast=force_forecast,
            summarize_limit=summarize_limit,
        )
    if summarize:
        _run_summarize(limit=summarize_limit)
    if forecast:
        _run_forecast(force=force_forecast)
    if show_data:
        _show_data()
    if serve:
        _serve_api()
    if worker:
        _run_worker()


def _run_test_ai() -> None:
    settings = get_settings()
    click.echo(f"Testing Gemini API ({settings.gemini_model})...")

    try:
        client = GeminiClient()
        result = client.ping()
    except GeminiAuthError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)
    except GeminiNetworkError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)
    except GeminiRateLimitError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)
    except GeminiClientError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    snippet = result.response_text[:120]
    click.echo("SUCCESS: Gemini API is reachable.")
    click.echo(f"Model: {result.model}")
    click.echo(f"Response: {snippet}{'...' if len(result.response_text) > 120 else ''}")


def _run_scraper(
    *,
    source: str | None,
    news_only: bool,
    macro_only: bool,
) -> None:
    click.echo("Running ingestion pipeline...")
    try:
        report = asyncio.run(
            run_full_ingestion(
                source=source,
                news_only=news_only,
                macro_only=macro_only,
            )
        )
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"ERROR: Ingestion failed: {exc}", err=True)
        sys.exit(1)

    _print_ingestion_report(report)


def _run_pipeline(
    *,
    source: str | None,
    skip_scrape: bool,
    news_only: bool,
    macro_only: bool,
    force_forecast: bool,
    summarize_limit: int | None,
) -> None:
    settings = get_settings()
    limit = summarize_limit or settings.summarize_batch_limit
    pending = get_unsummarized_count()
    click.echo("Running full pipeline (ingest → summarize → forecast)...")
    if pending:
        est_min = (min(pending, limit) * (settings.gemini_request_delay_seconds + 4)) / 60
        click.echo(
            f"Pending summarize: {pending} article(s), batch limit {limit} "
            f"(~{est_min:.1f} min for summarize step)"
        )
    try:
        report = asyncio.run(
            run_full_pipeline(
                source=source,
                skip_scrape=skip_scrape,
                news_only=news_only,
                macro_only=macro_only,
                force_forecast=force_forecast,
                summarize_limit=summarize_limit,
            )
        )
    except Exception as exc:  # noqa: BLE001
        click.echo(f"ERROR: Pipeline failed: {exc}", err=True)
        sys.exit(1)

    if report.ingestion:
        _print_ingestion_report(report.ingestion)

    if report.summarize:
        click.echo(
            f"Summarize: processed={report.summarize.processed}, "
            f"failed={report.summarize.failed}, "
            f"remaining={report.summarize.remaining}"
        )
        if report.summarize.remaining:
            click.echo(
                f"Tip: {report.summarize.remaining} article(s) still pending — "
                "run again or use --summarize-limit to increase batch."
            )

    if report.predict:
        click.echo(f"Forecast: {report.predict.message}")
        if report.predict.horizons_saved:
            _print_latest_forecasts()

    for error in report.errors:
        click.echo(f"ERROR: {error}", err=True)

    if report.errors:
        sys.exit(1)


def _run_summarize(*, limit: int | None) -> None:
    settings = get_settings()
    batch = limit or settings.summarize_batch_limit
    pending = get_unsummarized_count()
    click.echo(f"Summarizing up to {batch} of {pending} pending article(s)...")
    try:
        report = run_summarizer(limit=limit)
    except GeminiClientError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Summarize: processed={report.processed}, failed={report.failed}, "
        f"remaining={report.remaining}"
    )


def _run_forecast(*, force: bool) -> None:
    click.echo("Generating forecast...")
    try:
        report = run_predictor(force=force)
    except GeminiClientError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Forecast: {report.message}")
    if report.horizons_saved:
        _print_latest_forecasts()


def _print_ingestion_report(report) -> None:
    click.echo(
        f"Articles: inserted={report.articles_inserted}, "
        f"skipped={report.articles_skipped}"
    )
    click.echo(f"Macro saved: {report.macro_saved}")

    for run in report.scrape_runs:
        status = run.status.value
        detail = f"{run.source}: {status}"
        if run.article_count:
            detail += f" ({run.article_count} articles)"
        if run.duration_ms is not None:
            detail += f" [{run.duration_ms}ms]"
        if run.error and run.status != ScrapeStatus.SUCCESS:
            detail += f" — {run.error}"
        click.echo(detail)


def _print_latest_forecasts() -> None:
    forecasts = get_latest_forecasts()
    if not forecasts:
        return
    click.echo("Latest forecast:")
    for row in forecasts:
        click.echo(
            f"  {row['horizon']}: {row['trend']} "
            f"({row['confidence']}%) — {row['reasoning'][:80]}"
        )


def _show_data() -> None:
    counts = get_table_counts()
    click.echo("SQLite table counts:")
    for table, count in counts.items():
        click.echo(f"  {table}: {count}")

    macro = get_latest_macro()
    if macro:
        click.echo("Latest macro snapshot:")
        click.echo(f"  recorded_at: {macro.get('recorded_at')}")
        click.echo(f"  gold_spot: {macro.get('gold_spot')}")
        click.echo(f"  dxy: {macro.get('dxy')}")
        click.echo(f"  us10y: {macro.get('us10y')}")
        click.echo(f"  spdr_holdings: {macro.get('spdr_holdings')}")
    else:
        click.echo("Latest macro snapshot: (none)")

    forecasts = get_latest_forecasts()
    if forecasts:
        click.echo("Latest forecast horizons:")
        for row in forecasts:
            click.echo(
                f"  {row['horizon']}: {row['trend']} ({row['confidence']}%)"
            )
    else:
        click.echo("Latest forecast: (none)")


def _serve_api() -> None:
    settings = get_settings()
    click.echo(
        f"Starting API at http://{settings.api_host}:{settings.api_port} "
        "(Ctrl+C to stop)"
    )
    uvicorn.run(
        "src.backend.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


def _run_worker() -> None:
    click.echo("Starting ingestion scheduler (Ctrl+C to stop)...")
    start_scheduler()


if __name__ == "__main__":
    configure_logging()
    cli()
