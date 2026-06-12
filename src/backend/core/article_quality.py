"""Heuristics to skip low-quality scraped articles before Gemini calls."""

from __future__ import annotations

SKIPPED_SUMMARY_PREFIX = "[skipped]"

JUNK_TITLE_PHRASES = (
    "subscribe now",
    "sign in to read",
    "register to continue",
    "create your free account",
    "premium content",
    "access denied",
)

PAYWALL_SOURCES = frozenset({"bloomberg", "reuters"})

MIN_BODY_CHARS = {
    "bloomberg": 120,
    "reuters": 120,
}


def junk_article_reason(*, title: str, body: str, source: str) -> str | None:
    """Return a short reason when an article should not be summarized by Gemini."""
    title_normalized = title.strip().lower()
    body_stripped = body.strip()
    source_key = source.strip().lower()

    if not title_normalized:
        return "empty title"

    for phrase in JUNK_TITLE_PHRASES:
        if phrase in title_normalized:
            return f"junk title ({phrase})"

    min_chars = MIN_BODY_CHARS.get(source_key, 50)
    if len(body_stripped) < min_chars:
        return f"body too short ({len(body_stripped)} chars, min {min_chars})"

    return None
