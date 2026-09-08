"""Explicitly configured live market research boundary.

Live market observations are acquired only for research and are passed through
AletheiaTelos' existing market-data/evidence integrity pipeline. This module
contains no order, brokerage, credential, or portfolio execution capability.
"""

from datetime import datetime
from typing import Any, Dict, Iterable

from app.market_data import MarketDataSource
from app.market_data_pipeline import acquire_market_data


def live_market_research(
    source: MarketDataSource,
    symbols: Iterable[str],
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Acquire current provider observations without applying trading logic."""
    requested = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
    if not requested:
        raise ValueError("At least one market symbol is required.")

    result = acquire_market_data(
        source=source,
        symbols=requested,
        now=now,
        max_age_seconds=max_age_seconds,
    )
    result["research_only"] = True
    result["prediction_applied"] = False
    result["ranking_applied"] = False
    result["portfolio_execution"] = False
    result["human_decision_required"] = True
    return result
