"""Pipeline orchestration tests."""

import asyncio
from unittest.mock import AsyncMock, patch

from src.backend.core.models import IngestionReport
from src.backend.services.pipeline import run_full_pipeline
from src.backend.services.predictor import PredictReport
from src.backend.services.summarizer import SummarizeReport


def test_run_full_pipeline_skip_scrape():
    with (
        patch(
            "src.backend.services.pipeline.run_full_ingestion",
            new=AsyncMock(),
        ) as mock_ingest,
        patch(
            "src.backend.services.pipeline.run_summarizer",
            return_value=SummarizeReport(processed=2, failed=0),
        ),
        patch(
            "src.backend.services.pipeline.run_predictor",
            return_value=PredictReport(horizons_saved=4, message="saved"),
        ),
    ):
        report = asyncio.run(run_full_pipeline(skip_scrape=True))

    mock_ingest.assert_not_called()
    assert report.ingestion is None
    assert report.summarize is not None
    assert report.summarize.processed == 2
    assert report.predict is not None
    assert report.predict.horizons_saved == 4
    assert report.errors == []


def test_run_full_pipeline_with_ingestion():
    ingestion = IngestionReport(articles_inserted=3, articles_skipped=1, macro_saved=True)

    with (
        patch(
            "src.backend.services.pipeline.run_full_ingestion",
            new=AsyncMock(return_value=ingestion),
        ),
        patch(
            "src.backend.services.pipeline.run_summarizer",
            return_value=SummarizeReport(processed=1, failed=0),
        ),
        patch(
            "src.backend.services.pipeline.run_predictor",
            return_value=PredictReport(horizons_saved=4, message="saved"),
        ),
    ):
        report = asyncio.run(run_full_pipeline())

    assert report.ingestion is not None
    assert report.ingestion.articles_inserted == 3
