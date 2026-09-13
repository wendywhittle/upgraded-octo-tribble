"""Provider-neutral Opportunity -> Evidence Candidate boundary.

An acquired opportunity is a discovery artifact, not validated evidence. This
module creates pending evidence candidates from source material without
bypassing the existing evidence validation layer or decision gate.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable
import hashlib
import json

from app.evidence import validate_evidence


EVIDENCE_CANDIDATE_STATUS = "EVIDENCE_CANDIDATE"


def _fingerprint(value: Dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def opportunity_to_evidence_candidate(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """Create a pending evidence candidate without claiming validation."""
    opportunity_id = opportunity.get("opportunity_id")
    source = opportunity.get("source")
    source_url = opportunity.get("source_url", "")
    observed_at = opportunity.get("observed_at", "")
    provenance = opportunity.get("provenance")

    candidate_basis = {
        "opportunity_id": opportunity_id,
        "source": source,
        "source_url": source_url,
        "observed_at": observed_at,
        "claim": opportunity.get("claim"),
        "raw_source_reference": opportunity.get("raw_source_reference", ""),
        "payload": opportunity.get("property_attributes", {}),
    }
    evidence_id = f"EVID-CAND-{_fingerprint(candidate_basis)[:16]}"

    candidate = {
        "evidence_id": evidence_id,
        "opportunity_id": opportunity_id,
        "source": source,
        "source_url": source_url,
        "observed_at": observed_at,
        "claim": opportunity.get("claim"),
        "raw_source_reference": opportunity.get("raw_source_reference", ""),
        "provenance": dict(provenance) if isinstance(provenance, dict) else provenance,
        "evidence_status": EVIDENCE_CANDIDATE_STATUS,
        "validation_status": "PENDING",
        "decision_usable": False,
        "research_only": True,
        "human_authority_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
        "classification": "FACT_CANDIDATE" if opportunity.get("claim") else "UNRESOLVED_QUESTION",
    }
    return candidate


def validate_opportunity_evidence_candidate(
    candidate: Dict[str, Any], now=None, max_age_seconds: float = 24 * 60 * 60
) -> Dict[str, Any]:
    """Explicitly invoke the existing evidence validator for a candidate."""
    report = validate_evidence(candidate, now=now, max_age_seconds=max_age_seconds)
    result = dict(candidate)
    result["validation_status"] = "VALIDATED" if report["decision_usable"] else "BLOCKED"
    result["decision_usable"] = report["decision_usable"]
    result["validation"] = report
    return result


def opportunity_to_evidence_candidates(
    opportunities: Iterable[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """Create pending candidates only; validation remains a separate operation."""
    return [opportunity_to_evidence_candidate(item) for item in opportunities]
