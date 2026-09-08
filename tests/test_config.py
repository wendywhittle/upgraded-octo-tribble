from app.config import live_market_enabled, market_symbol_map, research_feed_urls


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


def test_live_market_data_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ALETHEIA_LIVE_MARKET_DATA", raising=False)
    assert live_market_enabled() is False


def test_live_market_data_requires_explicit_enablement(monkeypatch):
    monkeypatch.setenv("ALETHEIA_LIVE_MARKET_DATA", "true")
    assert live_market_enabled() is True


def test_market_symbol_map_parses_logical_provider_pairs(monkeypatch):
    monkeypatch.setenv("ALETHEIA_MARKET_SYMBOL_MAP", "SPX=^spx,VIX=^vix")
    assert market_symbol_map() == {"SPX": "^spx", "VIX": "^vix"}
