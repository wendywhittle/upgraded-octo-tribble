from datetime import datetime, timezone

from app.market_data import MarketObservation
from app.market_data_pipeline import acquire_market_data
from app.static_market_data import StaticMarketDataSource


NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)


def test_market_data_pipeline_accepts_fresh_point_in_time_observation():
    source = StaticMarketDataSource(
        [MarketObservation("SPX", 6500.0, NOW.isoformat(), "fixture")]
    )
    result = acquire_market_data(source, ["SPX"], now=NOW)
    assert result["decision_usable"] is True
    assert result["usable_evidence_count"] == 1
    assert result["reasoning_applied"] is False
    assert result["brokerage_connectivity"] is False


def test_market_data_pipeline_rejects_future_observation():
    future = NOW.replace(hour=19)
    source = StaticMarketDataSource(
        [MarketObservation("SPX", 6500.0, future.isoformat(), "fixture")]
    )
    result = acquire_market_data(source, ["SPX"], now=NOW)
    assert result["decision_usable"] is False
    assert result["usable_evidence_count"] == 0
