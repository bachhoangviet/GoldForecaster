"""Rotate across Gemini models when rate limits or overload are hit."""

from __future__ import annotations

import logging
import time
from typing import TypeVar

from pydantic import BaseModel

from src.backend.adapters.gemini_client import (
    GeminiClient,
    GeminiClientError,
    GeminiRateLimitError,
    GeminiUnavailableError,
    PingResult,
)

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (GeminiRateLimitError, GeminiUnavailableError)


def parse_model_chain(raw: str, *fallbacks: str) -> list[str]:
    """Parse comma-separated model names, dedupe while preserving order."""
    models = [part.strip() for part in raw.split(",") if part.strip()]
    for item in fallbacks:
        if item and item not in models:
            models.append(item)

    seen: set[str] = set()
    ordered: list[str] = []
    for model in models:
        if model not in seen:
            seen.add(model)
            ordered.append(model)
    return ordered


class GeminiModelPool:
    """Try models in order; rotate when a model returns 429 or 503."""

    def __init__(
        self,
        models: list[str],
        *,
        cooldown_seconds: float = 300.0,
        unavailable_cooldown_seconds: float = 60.0,
    ) -> None:
        if not models:
            raise GeminiClientError("No Gemini models configured for this task.")

        self._models = models
        self._cooldown_seconds = cooldown_seconds
        self._unavailable_cooldown_seconds = unavailable_cooldown_seconds
        self._cooldown_until: dict[str, float] = {}
        self._clients: dict[str, GeminiClient] = {}
        self.last_model_used: str = models[0]
        self.last_hit_rate_limit = False

    @property
    def models(self) -> list[str]:
        return list(self._models)

    def _client_for(self, model: str) -> GeminiClient:
        if model not in self._clients:
            self._clients[model] = GeminiClient(model=model)
        return self._clients[model]

    def _available_models(self) -> list[str]:
        now = time.time()
        return [
            model
            for model in self._models
            if self._cooldown_until.get(model, 0.0) <= now
        ]

    def _mark_cooldown(self, model: str, exc: GeminiRateLimitError | GeminiUnavailableError) -> None:
        if isinstance(exc, GeminiUnavailableError):
            wait = self._unavailable_cooldown_seconds
            reason = "503 unavailable"
        else:
            wait = self._cooldown_seconds
            reason = "429 rate limit"

        self._cooldown_until[model] = time.time() + wait
        logger.warning(
            "%s on %s — cooldown %.0fs, trying next model in chain",
            reason,
            model,
            wait,
        )

    def _wait_for_available_model(self) -> None:
        if self._available_models():
            return

        soonest = min(self._cooldown_until.values())
        wait = max(1.0, soonest - time.time())
        capped = min(wait, 60.0)
        logger.warning(
            "All %d model(s) in cooldown — waiting %.0fs",
            len(self._models),
            capped,
        )
        time.sleep(capped)

    def ping(self, prompt: str = "Reply with exactly: GoldForecaster online") -> PingResult:
        self.last_hit_rate_limit = False

        while True:
            self._wait_for_available_model()
            last_error: GeminiRateLimitError | GeminiUnavailableError | None = None

            for model in self._available_models():
                try:
                    result = self._client_for(model).ping(prompt=prompt)
                    self.last_model_used = model
                    return result
                except _RETRYABLE_ERRORS as exc:
                    self.last_hit_rate_limit = True
                    self._mark_cooldown(model, exc)
                    last_error = exc
                except GeminiClientError:
                    raise

            if last_error is not None:
                time.sleep(10)
                continue

            raise GeminiClientError("No Gemini models available to ping.")

    def generate_json(
        self,
        *,
        prompt: str,
        schema_model: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> T:
        """Generate JSON, rotating models on 429 or 503."""
        self.last_hit_rate_limit = False
        rounds_without_success = 0
        max_rounds = max(len(self._models) * 2, 4)

        while rounds_without_success < max_rounds:
            self._wait_for_available_model()
            last_error: GeminiRateLimitError | GeminiUnavailableError | None = None
            tried_any = False

            for model in self._available_models():
                tried_any = True
                try:
                    result = self._client_for(model).generate_json(
                        prompt=prompt,
                        schema_model=schema_model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_retries=1,
                    )
                    self.last_model_used = model
                    return result
                except _RETRYABLE_ERRORS as exc:
                    self.last_hit_rate_limit = True
                    self._mark_cooldown(model, exc)
                    last_error = exc
                except GeminiClientError:
                    raise

            if not tried_any or last_error is None:
                raise GeminiClientError("No Gemini models available for JSON generation.")

            rounds_without_success += 1
            logger.warning(
                "All available models busy (429/503) — round %d/%d, waiting 30s",
                rounds_without_success,
                max_rounds,
            )
            time.sleep(30)

        raise GeminiRateLimitError(
            "All Gemini models in the chain are unavailable. Retry later."
        )
