"""Deterministic market-data adapter for tests and local research fixtures."""

from typing import Iterable

from app.market_data import MarketObservation


class StaticMarketDataSource:
    """Read-only provider backed by supplied observations."""

    name = "static_market_data"

    def __init__(self, observations: Iterable[MarketObservation]):
        self._observations = tuple(observations)

    def snapshot(self, symbols: Iterable[str]) -> list[MarketObservation]:
        wanted = {symbol.strip().upper() for symbol in symbols if symbol.strip()}
        if not wanted:
            return []
        return [item for item in self._observations if item.symbol.upper() in wanted]


def source_status(source: StaticMarketDataSource) -> dict:
    return {
        "name": source.name,
        "read_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
    }
