"""Boundary adapter from validated financing observations to evidence.

This module deliberately does not validate financing claims itself. A
FinancingObservation must already be explicitly marked VALIDATED and carry an
evidence ID. The existing evidence validator then applies the repository's
normal provenance, timestamp, freshness, and decision-usability controls.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from app.evidence import validate_evidence
from app.financing_observation import FinancingObservation


def financing_observation_to_evidence(
    observation: FinancingObservation,
    *,
    retrieved_at: str | None = None,
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Convert an explicitly validated observation into existing evidence form.

    The adapter is provider-independent. It preserves the observation's
    provider, source, financing terms, assumptions, limitations, and timestamp
    inside the evidence payload and provenance. It never upgrades an
    unvalidated observation.
    """
    if not observation.is_validated_evidence:
        raise ValueError(
            "Only VALIDATED financing observations with evidence_id may cross the evidence boundary"
        )

    retrieved = retrieved_at or datetime.now(timezone.utc).isoformat()
    source = observation.source_uri or observation.source_label or observation.provider_id
    claim = {
        "financing_type": observation.financing_type,
        "asset_classes": list(observation.asset_classes),
        "geography": list(observation.geography),
        "loan_to_value": observation.loan_to_value,
        "loan_to_cost": observation.loan_to_cost,
        "interest_rate": observation.interest_rate,
        "term": observation.term,
        "amortization": observation.amortization,
        "covenants": list(observation.covenants),
        "assumptions": list(observation.assumptions),
        "limitations": list(observation.limitations),
    }
    evidence: Dict[str, Any] = {
        "evidence_id": observation.evidence_id,
        "source": source,
        "claim": claim,
        "observed_at": observation.observed_at,
        "retrieved_at": retrieved,
        "provenance": {
            "type": "external_source",
            "point_in_time": True,
            "provider_id": observation.provider_id,
            "observation_id": observation.observation_id,
            "source_uri": observation.source_uri,
            "source_label": observation.source_label,
            "financing_type": observation.financing_type,
            "asset_classes": list(observation.asset_classes),
            "geography": list(observation.geography),
            "assumptions": list(observation.assumptions),
            "limitations": list(observation.limitations),
            "validation_status": observation.validation_status,
        },
        "decision_usable": True,
    }

    validation = validate_evidence(
        evidence,
        now=now,
        max_age_seconds=max_age_seconds,
    )
    if not validation["decision_usable"]:
        raise ValueError(
            "Validated financing observation failed existing evidence validation: "
            + "; ".join(validation["errors"])
        )

    evidence["evidence_validation"] = validation
    return evidence
