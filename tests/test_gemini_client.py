"""Unit tests for Gemini client adapter."""

from unittest.mock import MagicMock, patch

import pytest

from src.backend.adapters.gemini_client import (
    GeminiAuthError,
    GeminiClient,
    GeminiClientError,
    PingResult,
)
from src.backend.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_ping_success():
    mock_response = MagicMock()
    mock_response.text = "GoldForecaster online"

    with patch("src.backend.adapters.gemini_client.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = mock_response
        client = GeminiClient(api_key="test-key", model="gemini-2.5-flash")
        result = client.ping()

    assert isinstance(result, PingResult)
    assert result.model == "gemini-2.5-flash"
    assert "GoldForecaster" in result.response_text


def test_ping_missing_api_key():
    with pytest.raises(GeminiAuthError):
        GeminiClient(api_key="")


def test_ping_empty_response():
    mock_response = MagicMock()
    mock_response.text = ""

    with patch("src.backend.adapters.gemini_client.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = mock_response
        client = GeminiClient(api_key="test-key")
        with pytest.raises(GeminiClientError, match="empty response"):
            client.ping()
