from datetime import datetime, timezone

import pytest

from app.live_market_research import live_market_research
from app.market_data import MarketObservation
from app.static_market_data import StaticMarketDataSource


NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)


def test_live_market_research_is_reasoning_and_execution_free():
    source = StaticMarketDataSource([
        MarketObservation("SPX", 6512.5, NOW.isoformat(), "fixture", retrieved_at=NOW.isoformat())
    ])
    result = live_market_research(source, ["spx"], now=NOW)
    assert result["decision_usable"] is True
    assert result["research_only"] is True
    assert result["prediction_applied"] is False
    assert result["ranking_applied"] is False
    assert result["portfolio_execution"] is False
    assert result["human_decision_required"] is True


def test_live_market_research_rejects_empty_symbol_set():
    source = StaticMarketDataSource([])
    with pytest.raises(ValueError, match="At least one market symbol"):
        live_market_research(source, [])
