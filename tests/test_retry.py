"""Retry decorator tests."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.backend.adapters.scraper_utils import MAX_RETRIES, fetch_html, retry_request


def test_retry_request_succeeds_on_third_attempt():
    calls = {"count": 0}

    @retry_request(max_retries=3, backoff_seconds=0)
    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.ConnectionError("network down")
        return "ok"

    assert flaky() == "ok"
    assert calls["count"] == 3


def test_retry_request_raises_after_max_attempts():
    calls = {"count": 0}

    @retry_request(max_retries=3, backoff_seconds=0)
    def flaky() -> str:
        calls["count"] += 1
        raise requests.exceptions.Timeout("timeout")

    with pytest.raises(requests.exceptions.Timeout):
        flaky()

    assert calls["count"] == MAX_RETRIES


def test_fetch_html_retries_on_failure():
    ok_response = MagicMock()
    ok_response.text = "<html>ok</html>"
    ok_response.raise_for_status = MagicMock()

    with (
        patch("src.backend.adapters.scraper_utils.requests.get") as mock_get,
        patch("src.backend.adapters.scraper_utils.time.sleep"),
    ):
        mock_get.side_effect = [
            requests.ConnectionError("down"),
            requests.ConnectionError("down"),
            ok_response,
        ]
        result = fetch_html("https://example.com")

    assert result == "<html>ok</html>"
    assert mock_get.call_count == 3
