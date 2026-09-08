from datetime import datetime, timezone

import pytest

from app.research import research_query
from app.rss_adapter import RSSFeedEvidenceSource


RSS = b'''<?xml version="1.0"?>
<rss version="2.0"><channel><title>Example Feed</title>
<item><title>Market update</title><description>Equity markets rise.</description><link>https://example.com/a</link><pubDate>Tue, 08 Sep 2026 12:00:00 GMT</pubDate></item>
</channel></rss>'''


NOW = datetime(2026, 9, 8, 14, 0, tzinfo=timezone.utc)


def test_research_query_preserves_research_only_boundary():
    source = RSSFeedEvidenceSource(
        ["https://feeds.example.com/news"], fetcher=lambda _: RSS
    )
    result = research_query(
        source,
        query="market",
        claim="Equity markets rise.",
        now=NOW,
    )
    assert result["decision_usable"] is True
    assert result["research_only"] is True
    assert result["write_capability"] is False
    assert result["order_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["reasoning_applied"] is False


def test_research_query_rejects_empty_inputs():
    source = RSSFeedEvidenceSource(
        ["https://feeds.example.com/news"], fetcher=lambda _: RSS
    )
    with pytest.raises(ValueError):
        research_query(source, "", "A claim", now=NOW)
    with pytest.raises(ValueError):
        research_query(source, "market", "", now=NOW)
