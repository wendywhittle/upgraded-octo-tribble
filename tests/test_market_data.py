from app.market_data import MarketObservation, observations_to_evidence
from app.static_market_data import StaticMarketDataSource, source_status


def test_market_observation_normalizes_symbol_and_timestamp():
    observation = MarketObservation(
        symbol="spx",
        price=6500.25,
        observed_at="2026-09-08T14:00:00-04:00",
        source="fixture",
        currency="USD",
        timeframe="1d",
    )
    item = observation.normalized()
    assert item["symbol"] == "SPX"
    assert item["observed_at"] == "2026-09-08T18:00:00+00:00"


def test_market_observations_become_provenance_rich_evidence():
    observation = MarketObservation(
        symbol="SPX",
        price=6500.25,
        observed_at="2026-09-08T14:00:00+00:00",
        source="fixture",
        url="https://example.com/market",
    )
    evidence = observations_to_evidence([observation])
    assert evidence[0]["provenance"]["type"] == "market_data"
    assert evidence[0]["provenance"]["point_in_time"] is True
    assert evidence[0]["provenance"]["symbol"] == "SPX"


def test_static_market_source_is_read_only_and_filters_symbols():
    source = StaticMarketDataSource(
        [
            MarketObservation("SPX", 6500.0, "2026-09-08T14:00:00+00:00", "fixture"),
            MarketObservation("VIX", 18.0, "2026-09-08T14:00:00+00:00", "fixture"),
        ]
    )
    result = source.snapshot(["spx"])
    assert len(result) == 1
    assert result[0].symbol == "SPX"
    assert source_status(source)["read_only"] is True
    assert source_status(source)["execution_capability"] is False
    assert source_status(source)["brokerage_connectivity"] is False
