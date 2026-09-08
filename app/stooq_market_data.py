"""Read-only Stooq CSV market-data provider.

Stooq is used here as an external observation source only. The adapter fetches
historical/daily quote data and converts it into the existing MarketObservation
contract. It cannot place orders, access brokerage credentials, or mutate
remote market state.
"""

from datetime import datetime, timezone
from io import StringIO
from typing import Callable, Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen
import csv

from app.market_data import MarketObservation


class StooqMarketDataSource:
    name = "stooq"

    def __init__(
        self,
        symbol_map: dict[str, str] | None = None,
        fetch: Callable[[str], str] | None = None,
        timeout_seconds: float = 10.0,
    ):
        self._symbol_map = {k.upper(): v for k, v in (symbol_map or {}).items()}
        self._fetch = fetch or self._http_get
        self._timeout_seconds = timeout_seconds

    def _http_get(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "AletheiaTelos/1.0"})
        with urlopen(request, timeout=self._timeout_seconds) as response:
            return response.read().decode("utf-8")

    def _provider_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        return self._symbol_map.get(normalized, normalized.lower())

    def _url(self, provider_symbol: str) -> str:
        return "https://stooq.com/q/d/l/?s=" + quote(provider_symbol, safe="") + "&i=d"

    @staticmethod
    def _parse_latest(symbol: str, source_url: str, text: str) -> MarketObservation:
        rows = list(csv.DictReader(StringIO(text)))
        if not rows:
            raise ValueError(f"Stooq returned no rows for {symbol}.")
        row = rows[-1]
        date_value = (row.get("Date") or "").strip()
        close_value = (row.get("Close") or "").strip()
        if not date_value or not close_value:
            raise ValueError(f"Stooq response missing Date or Close for {symbol}.")
        try:
            price = float(close_value)
            observed_date = datetime.strptime(date_value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError(f"Invalid Stooq observation for {symbol}.") from exc
        return MarketObservation(
            symbol=symbol,
            price=price,
            observed_at=observed_date.isoformat(),
            source="stooq",
            url=source_url,
            currency="USD",
            timeframe="1d",
            source_identity="stooq.com",
            point_in_time=True,
        )

    def snapshot(self, symbols: Iterable[str]) -> list[MarketObservation]:
        observations: list[MarketObservation] = []
        for raw_symbol in symbols:
            symbol = raw_symbol.strip().upper()
            if not symbol:
                continue
            provider_symbol = self._provider_symbol(symbol)
            url = self._url(provider_symbol)
            text = self._fetch(url)
            observations.append(self._parse_latest(symbol, url, text))
        return observations


def source_status(source: StooqMarketDataSource) -> dict:
    return {
        "name": source.name,
        "read_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "external_network": True,
    }
