"""Provider-neutral opportunity acquisition boundary.

Acquisition discovers candidate opportunities; it does not decide, transact, or
claim that an opportunity is evidence. External source adapters can be added at
this seam later using permitted, licensed, or authorized access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Iterable, Protocol


ACQUISITION_STAGES = (
    "DISCOVERED",
    "NORMALIZED",
    "DEDUPLICATED",
    "EVIDENCE_PENDING",
    "EVIDENCE_VALIDATED",
    "INVESTIGATION",
    "UNDERWRITING",
    "IC",
    "CLOSED",
    "REJECTED",
    "ARCHIVED",
)


@dataclass(frozen=True)
class RawObservation:
    """A source observation before it becomes a normalized opportunity."""

    source: str
    source_url: str = ""
    observed_at: str = ""
    payload: Dict[str, Any] | None = None


class OpportunityAdapter(Protocol):
    """Contract for a permitted/licensed/authorized acquisition source."""

    source_name: str

    def discover(self) -> Iterable[RawObservation]:
        ...


def _timestamp(value: str = "") -> str:
    return value or datetime.now(timezone.utc).isoformat()


def _fingerprint(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_observation(observation: RawObservation) -> Dict[str, Any]:
    """Normalize a raw observation without treating it as validated evidence."""
    payload = dict(observation.payload or {})
    content_fingerprint = _fingerprint(
        {
            "source": observation.source,
            "source_url": observation.source_url,
            "payload": payload,
        }
    )
    opportunity_id = f"OPP-{content_fingerprint[:16]}"
    return {
        "opportunity_id": opportunity_id,
        "asset_type": str(payload.get("asset_type", "")).strip(),
        "source": observation.source,
        "source_url": observation.source_url,
        "discovered_at": _timestamp(),
        "observed_at": _timestamp(observation.observed_at),
        "location": payload.get("location", ""),
        "asking_price": payload.get("asking_price"),
        "property_attributes": payload.get("property_attributes", {}),
        "seller_or_broker": payload.get("seller_or_broker", {}),
        "claim": payload.get("claim"),
        "raw_source_reference": payload.get("raw_source_reference", ""),
        "content_fingerprint": content_fingerprint,
        "provenance": {
            "source": observation.source,
            "source_url": observation.source_url,
            "observed_at": _timestamp(observation.observed_at),
            "raw_observation_present": True,
        },
        "acquisition_status": "NORMALIZED",
        "evidence_status": "PENDING",
        "research_only": True,
        "human_authority_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    }


def deduplicate(opportunities: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Keep the first observation for each content fingerprint."""
    seen: set[str] = set()
    result: list[Dict[str, Any]] = []
    for opportunity in opportunities:
        fingerprint = opportunity["content_fingerprint"]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        item = dict(opportunity)
        item["acquisition_status"] = "DEDUPLICATED"
        result.append(item)
    return result


def acquire(observations: Iterable[RawObservation]) -> Dict[str, Any]:
    """Run the acquisition boundary through normalization and deduplication."""
    raw = list(observations)
    normalized = [normalize_observation(item) for item in raw]
    opportunities = deduplicate(normalized)
    return {
        "system": "AletheiaTelos",
        "layer": "opportunity_acquisition",
        "raw_observation_count": len(raw),
        "normalized_count": len(normalized),
        "deduplicated_count": len(opportunities),
        "opportunities": opportunities,
        "evidence_validation_required": True,
        "opportunity_is_not_evidence": True,
        "research_only": True,
        "human_authority_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
        "audit": {
            "pipeline": "source->raw_observation->normalization->deduplication->provenance->opportunity->evidence_validation",
            "external_source_access": "adapter boundary only",
            "execution_capability": False,
        },
    }
