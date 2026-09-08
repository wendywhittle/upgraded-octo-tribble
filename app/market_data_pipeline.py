"""Market-data ingestion boundary.

This layer converts read-only market observations into evidence and applies the
existing integrity validator. It deliberately performs no prediction, ranking,
portfolio construction, or execution.
"""

from datetime import datetime
from typing import Any, Dict, Iterable

from app.evidence import validate_evidence
from app.market_data import MarketDataSource, observations_to_evidence


def acquire_market_data(
    source: MarketDataSource,
    symbols: Iterable[str],
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    observations = list(source.snapshot(symbols))
    evidence = observations_to_evidence(observations)
    validation = [
        validate_evidence(item, now=now, max_age_seconds=max_age_seconds)
        for item in evidence
    ]
    usable = [item for item, report in zip(evidence, validation) if report["decision_usable"]]

    return {
        "source": source.name,
        "symbols": [item.symbol.upper() for item in observations],
        "observation_count": len(observations),
        "evidence_count": len(evidence),
        "usable_evidence_count": len(usable),
        "decision_usable": bool(evidence) and len(usable) == len(evidence),
        "observations": [item.normalized() for item in observations],
        "evidence": evidence,
        "validation": validation,
        "reasoning_applied": False,
        "read_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
    }
