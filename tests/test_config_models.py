"""Tests for per-task Gemini model settings."""

from src.backend.core.config import DEFAULT_FORECAST_MODELS, DEFAULT_SUMMARIZE_MODELS, get_settings


def test_effective_models_use_default_chains(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.delenv("GEMINI_SUMMARIZE_MODELS", raising=False)
    monkeypatch.delenv("GEMINI_FORECAST_MODELS", raising=False)
    monkeypatch.delenv("GEMINI_SUMMARIZE_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_FORECAST_MODEL", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.effective_summarize_models[0] == "gemini-3.1-flash-lite"
    assert "gemma-4-26b" in settings.effective_summarize_models
    assert settings.effective_summarize_models == settings.effective_summarize_models
    assert DEFAULT_SUMMARIZE_MODELS.startswith("gemini-3.1-flash-lite")
    assert settings.effective_forecast_models[0] == "gemini-3.5-flash"
    assert DEFAULT_FORECAST_MODELS.startswith("gemini-3.5-flash")
    get_settings.cache_clear()


def test_effective_models_use_custom_chains(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv(
        "GEMINI_SUMMARIZE_MODELS",
        "gemini-a,gemini-b",
    )
    monkeypatch.setenv(
        "GEMINI_FORECAST_MODELS",
        "gemini-x,gemini-y",
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.effective_summarize_models[:2] == ["gemini-a", "gemini-b"]
    assert settings.effective_forecast_models[:2] == ["gemini-x", "gemini-y"]
    get_settings.cache_clear()
