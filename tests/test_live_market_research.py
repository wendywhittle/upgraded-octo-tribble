from datetime import datetime, timezone

import pytest

from app.live_market_research import live_market_research
from app.market_data import MarketObservation


NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)


class StaticSource:
    name = "test"

    def snapshot(self, symbols):
        return [
            MarketObservation(
                symbol=symbol,
                price=100.0,
                observed_at="2026-09-08T17:00:00+00:00",
                retrieved_at=NOW.isoformat(),
                source="test",
                source_identity="test.example",
                point_in_time=True,
            )
            for symbol in symbols
        ]


def test_live_market_research_is_not_execution_or_prediction():
    result = live_market_research(StaticSource(), ["SPX"], now=NOW)
    assert result["research_only"] is True
    assert result["prediction_applied"] is False
    assert result["ranking_applied"] is False
    assert result["portfolio_execution"] is False
    assert result["human_decision_required"] is True
    assert result["brokerage_connectivity"] is False


def test_live_market_research_rejects_empty_symbols():
    with pytest.raises(ValueError, match="At least one market symbol"):
        live_market_research(StaticSource(), [])
