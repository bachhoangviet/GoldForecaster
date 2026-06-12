"""Tests for Gemini model fallback pool."""

from unittest.mock import MagicMock, patch

import pytest

from src.backend.adapters.gemini_client import GeminiRateLimitError, GeminiUnavailableError
from src.backend.adapters.gemini_model_pool import GeminiModelPool, parse_model_chain
from src.backend.core.ai_models import ArticleSummaryResult


def test_parse_model_chain_dedupes_and_preserves_order():
    chain = parse_model_chain(
        "gemini-a, gemini-b, gemini-a",
        "gemini-c",
    )
    assert chain == ["gemini-a", "gemini-b", "gemini-c"]


def test_pool_switches_model_on_rate_limit():
    mock_result = ArticleSummaryResult(summary="- Gold steady", sentiment="neutral")

    first_client = MagicMock()
    first_client.generate_json.side_effect = GeminiRateLimitError("429")

    second_client = MagicMock()
    second_client.generate_json.return_value = mock_result

    with patch("src.backend.adapters.gemini_model_pool.GeminiClient") as mock_client_cls:
        mock_client_cls.side_effect = [first_client, second_client]
        pool = GeminiModelPool(
            ["gemini-a", "gemini-b"],
            cooldown_seconds=60,
        )
        result = pool.generate_json(
            prompt="test",
            schema_model=ArticleSummaryResult,
        )

    assert result.sentiment == "neutral"
    assert pool.last_model_used == "gemini-b"
    assert pool.last_hit_rate_limit is True


def test_pool_switches_model_on_503():
    mock_result = ArticleSummaryResult(summary="- Gold steady", sentiment="neutral")

    first_client = MagicMock()
    first_client.generate_json.side_effect = GeminiUnavailableError("503")

    second_client = MagicMock()
    second_client.generate_json.return_value = mock_result

    with patch("src.backend.adapters.gemini_model_pool.GeminiClient") as mock_client_cls:
        mock_client_cls.side_effect = [first_client, second_client]
        pool = GeminiModelPool(
            ["gemini-3.5-flash", "gemini-3.1-flash-lite"],
            cooldown_seconds=300,
            unavailable_cooldown_seconds=60,
        )
        result = pool.generate_json(
            prompt="test",
            schema_model=ArticleSummaryResult,
        )

    assert result.sentiment == "neutral"
    assert pool.last_model_used == "gemini-3.1-flash-lite"
    assert pool.last_hit_rate_limit is True


def test_pool_requires_models():
    with pytest.raises(Exception, match="No Gemini models"):
        GeminiModelPool([])
