"""Gemini API client adapter using the official google-genai SDK."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import TypeVar

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from src.backend.core.config import get_settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GeminiClientError(Exception):
    """Base error for Gemini adapter failures."""


class GeminiAuthError(GeminiClientError):
    """Invalid or missing API key."""


class GeminiNetworkError(GeminiClientError):
    """Network connectivity failure."""


class GeminiRateLimitError(GeminiClientError):
    """API rate limit exceeded."""


@dataclass
class PingResult:
    model: str
    response_text: str


def _map_exception(exc: Exception) -> GeminiClientError:
    message = str(exc)
    lowered = message.lower()

    if isinstance(exc, genai_errors.ClientError):
        if exc.code == 429 or "rate" in lowered or "quota" in lowered:
            return GeminiRateLimitError(
                "Gemini API rate limit reached. Retry later or check AI Studio quota."
            )
        if exc.code in (401, 403) or "api key" in lowered or "permission" in lowered:
            return GeminiAuthError(
                "Gemini API key is invalid or missing. Set GEMINI_API_KEY in .env."
            )

    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return GeminiNetworkError(f"Network error while calling Gemini API: {message}")

    if "429" in message or "resource_exhausted" in lowered:
        return GeminiRateLimitError(
            "Gemini API rate limit reached. Retry later or check AI Studio quota."
        )
    if "api key" in lowered or "unauthorized" in lowered:
        return GeminiAuthError(
            "Gemini API key is invalid or missing. Set GEMINI_API_KEY in .env."
        )

    return GeminiClientError(f"Gemini API call failed: {message}")


class GeminiClient:
    """Thin wrapper around google-genai Client."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

        if not self.api_key or self.api_key == "your_key_here":
            raise GeminiAuthError(
                "GEMINI_API_KEY is not configured. Copy .env.example to .env and add your key."
            )

        self._client = genai.Client(api_key=self.api_key)

    def ping(self, prompt: str = "Reply with exactly: GoldForecaster online") -> PingResult:
        """Send a short prompt to verify API connectivity."""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as exc:  # noqa: BLE001 - mapped to domain errors
            raise _map_exception(exc) from exc

        text = (response.text or "").strip()
        if not text:
            raise GeminiClientError("Gemini API returned an empty response.")

        return PingResult(model=self.model, response_text=text)

    def generate_json(
        self,
        *,
        prompt: str,
        schema_model: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_retries: int = 5,
    ) -> T:
        """Generate structured JSON and validate with a Pydantic model."""
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            system_instruction=system_instruction,
        )
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                raw = (response.text or "").strip()
                if not raw:
                    raise GeminiClientError("Gemini API returned empty JSON response.")
                payload = json.loads(raw)
                return schema_model.model_validate(payload)
            except json.JSONDecodeError as exc:
                last_error = GeminiClientError(f"Invalid JSON from Gemini: {exc}")
            except ValidationError as exc:
                last_error = GeminiClientError(f"Schema validation failed: {exc}")
            except Exception as exc:  # noqa: BLE001
                mapped = _map_exception(exc)
                if isinstance(mapped, GeminiRateLimitError):
                    last_error = mapped
                    if attempt < max_retries:
                        wait = min(90, 20 * attempt)
                        logger.warning(
                            "Gemini 429 rate limit — retry %d/%d in %ds",
                            attempt,
                            max_retries,
                            wait,
                        )
                        time.sleep(wait)
                        continue
                    raise mapped from exc
                last_error = mapped

            if attempt < max_retries:
                time.sleep(2 * attempt)

        assert last_error is not None
        raise last_error
