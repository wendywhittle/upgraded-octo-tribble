import os

from app.config import research_feed_urls


def test_research_feed_urls_reads_comma_separated_environment(monkeypatch):
    monkeypatch.setenv(
        "ALETHEIA_RESEARCH_FEEDS",
        " https://example.com/a ,https://example.com/b ",
    )
    assert research_feed_urls() == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_research_feed_urls_is_empty_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ALETHEIA_RESEARCH_FEEDS", raising=False)
    assert research_feed_urls() == []
