from datetime import datetime, timezone

import pytest

from app.stooq_market_data import StooqMarketDataSource, source_status


CSV = "Date,Open,High,Low,Close,Volume\n2026-09-08,6500,6520,6480,6512.5,1000\n"
NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)


def test_stooq_adapter_parses_daily_close_without_network():
    source = StooqMarketDataSource(fetch=lambda url: CSV, clock=lambda: NOW)
    result = source.snapshot(["SPX"])
    assert len(result) == 1
    assert result[0].symbol == "SPX"
    assert result[0].price == 6512.5
    assert result[0].observed_at == "2026-09-08T00:00:00+00:00"
    assert result[0].retrieved_at == NOW.isoformat()
    assert result[0].source_identity == "stooq.com"
    assert result[0].timeframe == "1d"


def test_stooq_adapter_supports_provider_symbol_mapping():
    seen = []

    def fetch(url):
        seen.append(url)
        return CSV

    source = StooqMarketDataSource(symbol_map={"SPX": "^spx"}, fetch=fetch, clock=lambda: NOW)
    source.snapshot(["spx"])
    assert "s=%5Espx" in seen[0]


def test_stooq_adapter_rejects_malformed_payload():
    source = StooqMarketDataSource(fetch=lambda url: "Date,Open,High,Low,Close,Volume\n")
    with pytest.raises(ValueError, match="no rows"):
        source.snapshot(["SPX"])


@pytest.mark.parametrize("close_value", ["nan", "inf", "-inf", "0", "-1"])
def test_stooq_adapter_rejects_invalid_prices(close_value):
    payload = f"Date,Open,High,Low,Close,Volume\n2026-09-08,1,1,1,{close_value},100\n"
    source = StooqMarketDataSource(fetch=lambda url: payload, clock=lambda: NOW)
    with pytest.raises(ValueError, match="Invalid Stooq price"):
        source.snapshot(["SPX"])


def test_stooq_adapter_is_read_only():
    source = StooqMarketDataSource(fetch=lambda url: CSV, clock=lambda: NOW)
    status = source_status(source)
    assert status["read_only"] is True
    assert status["execution_capability"] is False
    assert status["brokerage_connectivity"] is False
    assert status["external_network"] is True
