from app.rss_adapter import RSSFeedEvidenceSource


RSS = b'''<?xml version="1.0"?>
<rss version="2.0"><channel><title>Example Feed</title>
<item><title>Market update</title><description>Equity markets rise.</description><link>https://example.com/a</link><pubDate>Tue, 08 Sep 2026 12:00:00 GMT</pubDate></item>
<item><title>Credit note</title><description>Credit risk increases.</description><link>https://example.com/b</link><pubDate>Tue, 08 Sep 2026 13:00:00 GMT</pubDate></item>
</channel></rss>'''


def test_rss_adapter_normalizes_entries():
    source = RSSFeedEvidenceSource(["https://feeds.example.com/news"], fetcher=lambda _: RSS)
    result = source.acquire("market", limit=5)
    assert len(result) == 1
    assert result[0].source == "Example Feed"
    assert result[0].title == "Market update"
    assert result[0].observed_at == "2026-09-08T12:00:00+00:00"
    assert result[0].point_in_time is True
    assert result[0].url == "https://example.com/a"


def test_rss_adapter_rejects_non_https_feed():
    try:
        RSSFeedEvidenceSource(["http://feeds.example.com/news"])
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("non-HTTPS feed URL should be rejected")


def test_rss_adapter_returns_no_matches_when_query_is_absent():
    source = RSSFeedEvidenceSource(["https://feeds.example.com/news"], fetcher=lambda _: RSS)
    result = source.acquire("volatility", limit=5)
    assert result == []
