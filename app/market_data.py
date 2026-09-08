"""Read-only market-data acquisition primitives.

Market data enters AletheiaTelos through the same evidence boundary as other
external information. This module defines the normalized market snapshot and a
provider protocol; it performs no trading, order placement, or brokerage work.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Protocol


@dataclass(frozen=True)
class MarketObservation:
    symbol: str
    price: float
    observed_at: str
    source: str
    url: str | None = None
    currency: str | None = None
    timeframe: str | None = None
    source_identity: str | None = None
    point_in_time: bool = True
    retrieved_at: str | None = None

    def normalized(self) -> Dict[str, Any]:
        observed = self.observed_at
        if observed:
            parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            observed = parsed.astimezone(timezone.utc).isoformat()
        retrieved = self.retrieved_at
        if retrieved:
            parsed = datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            retrieved = parsed.astimezone(timezone.utc).isoformat()
        return {**asdict(self), "symbol": self.symbol.upper(), "observed_at": observed, "retrieved_at": retrieved}


class MarketDataSource(Protocol):
    """Contract for read-only market-data providers."""

    name: str

    def snapshot(self, symbols: Iterable[str]) -> Iterable[MarketObservation]:
        ...


def observations_to_evidence(observations: Iterable[MarketObservation]) -> list[Dict[str, Any]]:
    """Represent market observations as evidence records without adding reasoning."""
    evidence = []
    for index, observation in enumerate(observations, start=1):
        item = observation.normalized()
        evidence.append(
            {
                "evidence_id": f"market-{item['symbol'].lower()}-{index}",
                "source": item["source"],
                "claim": f"{item['symbol']} price observed at {item['price']}",
                "observed_at": item["observed_at"],
                "retrieved_at": item.get("retrieved_at") or item["observed_at"],
                "provenance": {
                    "type": "market_data",
                    "point_in_time": item["point_in_time"],
                    "source_identity": item.get("source_identity") or item["source"],
                    "url": item.get("url"),
                    "symbol": item["symbol"],
                    "currency": item.get("currency"),
                    "timeframe": item.get("timeframe"),
                },
            }
        )
    return evidence
