"""Research-only evidence acquisition service.

External information enters AletheiaTelos only through an EvidenceSource and the
integrity pipeline. This module exposes no write, order, or brokerage capability.
"""

from datetime import datetime
from typing import Any, Dict

from app.evidence_pipeline import acquire_evidence
from app.evidence_sources import EvidenceSource


def research_query(
    source: EvidenceSource,
    query: str,
    claim: str,
    limit: int = 10,
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Run a read-only research query through the evidence integrity boundary."""
    if not query.strip():
        raise ValueError("Research query cannot be empty.")
    if not claim.strip():
        raise ValueError("Research claim cannot be empty.")

    result = acquire_evidence(
        source=source,
        query=query,
        claim=claim,
        limit=limit,
        now=now,
        max_age_seconds=max_age_seconds,
    )
    result["research_only"] = True
    result["write_capability"] = False
    result["order_capability"] = False
    result["brokerage_connectivity"] = False
    return result
