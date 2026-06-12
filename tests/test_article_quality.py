"""Tests for junk article detection."""

from src.backend.core.article_quality import junk_article_reason


def test_subscribe_now_title_is_junk():
    reason = junk_article_reason(
        title="SUBSCRIBE NOW",
        body="Long enough body text " * 10,
        source="bloomberg",
    )
    assert reason is not None
    assert "subscribe now" in reason


def test_short_bloomberg_body_is_junk():
    reason = junk_article_reason(
        title="Gold market update",
        body="Short paywall stub.",
        source="bloomberg",
    )
    assert reason is not None
    assert "too short" in reason


def test_valid_kitco_article_is_not_junk():
    reason = junk_article_reason(
        title="Gold rises on weak dollar",
        body="Gold prices moved higher as the dollar weakened across major trading pairs today.",
        source="kitco",
    )
    assert reason is None
