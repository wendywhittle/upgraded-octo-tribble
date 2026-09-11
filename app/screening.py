"""Immutable CRE opportunity screening boundary.

Screening is a research filter between opportunity/evidence and deeper
underwriting. It determines whether an opportunity warrants additional
analysis; it does not authorize investment or execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.cre_evidence import CREEvidence
from app.opportunity import CREOpportunityDeal

ScreeningDisposition = Literal["PASS", "FAIL", "HOLD", "INSUFFICIENT_DATA"]
ScreeningCriterionStatus = Literal[
    "satisfied",
    "not_satisfied",
    "unresolved",
    "missing_evidence",
    "conflicting_evidence",
    "stale_or_unsuitable_evidence",
    "not_applicable",
]
ScreeningEpistemicStatus = Literal[
    "observed", "sourced", "assumed", "unresolved", "superseded"
]


class ScreeningCriterion(BaseModel):
    """One explicit screening criterion and its current evidence state."""

    model_config = ConfigDict(frozen=True)

    criterion_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: ScreeningCriterionStatus
    epistemic_status: ScreeningEpistemicStatus
    value: str | int | float | bool | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: str | None = None
    uncertainty: list[str] = Field(default_factory=list)
    critical: bool = False


class CREOpportunityScreening(BaseModel):
    """Canonical immutable screening result for a CRE opportunity."""

    model_config = ConfigDict(frozen=True)

    screening_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    created_at: datetime
    criteria: list[ScreeningCriterion] = Field(default_factory=list)
    disposition: ScreeningDisposition
    positive_factors: list[str] = Field(default_factory=list)
    negative_factors: list[str] = Field(default_factory=list)
    unresolved_factors: list[str] = Field(default_factory=list)
    missing_critical_evidence: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    supersedes_screening_id: str | None = Field(default=None, min_length=1)
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    transaction_capability: Literal[False] = False
    authorization_capability: Literal[False] = False


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def build_cre_opportunity_screening(
    *,
    screening_id: str,
    opportunity_id: str,
    criteria: list[ScreeningCriterion] | None = None,
    disposition: ScreeningDisposition,
    positive_factors: list[str] | None = None,
    negative_factors: list[str] | None = None,
    unresolved_factors: list[str] | None = None,
    missing_critical_evidence: list[str] | None = None,
    risk_flags: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    uncertainty: list[str] | None = None,
    supersedes_screening_id: str | None = None,
    created_at: datetime | None = None,
) -> CREOpportunityScreening:
    """Construct a screening artifact without inferring unavailable facts."""
    records = list(criteria or [])
    refs = list(evidence_refs or [])
    for criterion in records:
        refs.extend(criterion.evidence_refs)
    return CREOpportunityScreening(
        screening_id=screening_id,
        opportunity_id=opportunity_id,
        created_at=created_at or utc_now(),
        criteria=records,
        disposition=disposition,
        positive_factors=list(dict.fromkeys(positive_factors or [])),
        negative_factors=list(dict.fromkeys(negative_factors or [])),
        unresolved_factors=list(dict.fromkeys(unresolved_factors or [])),
        missing_critical_evidence=list(dict.fromkeys(missing_critical_evidence or [])),
        risk_flags=list(dict.fromkeys(risk_flags or [])),
        evidence_refs=list(dict.fromkeys(refs)),
        uncertainty=list(dict.fromkeys(uncertainty or [])),
        supersedes_screening_id=supersedes_screening_id,
    )


def validate_screening_scope(
    screening: CREOpportunityScreening,
    opportunity: CREOpportunityDeal,
    cre_evidence: list[CREEvidence] | None = None,
) -> None:
    """Validate only identity/reference compatibility, never infer a disposition."""
    if screening.opportunity_id != opportunity.opportunity_id:
        raise ValueError("screening opportunity_id must match the canonical opportunity")
    evidence_ids = {item.evidence_id for item in (cre_evidence or [])}
    unknown_refs = set(screening.evidence_refs) - evidence_ids
    if cre_evidence is not None and unknown_refs:
        raise ValueError(f"screening references unknown CRE evidence: {sorted(unknown_refs)}")
