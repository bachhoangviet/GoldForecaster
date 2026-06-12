"""Tests for Gemini structured output models."""

from src.backend.core.ai_models import ArticleSummaryResult


def test_article_summary_coerces_list_to_string():
    result = ArticleSummaryResult.model_validate(
        {
            "summary": [
                "Dollar weakness supports gold",
                "- ETF inflows remain steady",
            ],
            "sentiment": "bullish",
        }
    )

    assert result.sentiment == "bullish"
    assert result.summary.startswith("- Dollar weakness supports gold")
    assert "- ETF inflows remain steady" in result.summary
