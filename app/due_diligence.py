"""Immutable CRE property due diligence representation.

Due diligence records findings about an opportunity/property. They remain
analytical and non-authoritative, and never silently become assumptions or
investment decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.cre_evidence import CREEvidence
from app.opportunity import CREOpportunityDeal
from app.screening import CREOpportunityScreening

DueDiligenceCategory = Literal[
    "physical", "environmental", "legal", "zoning", "title", "tenancy",
    "lease", "financial", "operational", "market", "insurance", "other",
]
DueDiligenceEpistemicStatus = Literal["observed", "sourced", "unresolved", "superseded"]
DueDiligenceReviewStatus = Literal["not_started", "in_progress", "completed", "unresolved", "not_applicable"]
Materiality = Literal["low", "medium", "high", "unknown"]


class DueDiligenceProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    uncertainty: list[str] = Field(default_factory=list)


class DueDiligenceFinding(BaseModel):
    """One immutable property-level finding."""

    model_config = ConfigDict(frozen=True)

    finding_id: str = Field(min_length=1)
    category: DueDiligenceCategory
    field_name: str = Field(min_length=1)
    status: DueDiligenceEpistemicStatus
    review_status: DueDiligenceReviewStatus = "not_started"
    finding: str | None = None
    observed_value: str | int | float | bool | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    materiality: Materiality = "unknown"
    risk_flag: str | None = None
    unresolved_reason: str | None = None
    conflict_refs: list[str] = Field(default_factory=list)
    supersedes_finding_id: str | None = Field(default=None, min_length=1)
    provenance: DueDiligenceProvenance | None = None


class CREPropertyDueDiligence(BaseModel):
    """Canonical immutable property due diligence artifact."""

    model_config = ConfigDict(frozen=True)

    due_diligence_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    property_id: str | None = Field(default=None, min_length=1)
    created_at: datetime
    findings: list[DueDiligenceFinding] = Field(default_factory=list)
    unknown_fields: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    supersedes_due_diligence_id: str | None = Field(default=None, min_length=1)
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    transaction_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    authorization_capability: Literal[False] = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_cre_property_due_diligence(
    *,
    due_diligence_id: str,
    opportunity_id: str,
    property_id: str | None = None,
    findings: list[DueDiligenceFinding] | None = None,
    unknown_fields: list[str] | None = None,
    missing_documents: list[str] | None = None,
    unresolved_items: list[str] | None = None,
    conflict_refs: list[str] | None = None,
    uncertainty: list[str] | None = None,
    supersedes_due_diligence_id: str | None = None,
    created_at: datetime | None = None,
) -> CREPropertyDueDiligence:
    records = list(findings or [])
    refs = list(conflict_refs or [])
    for finding in records:
        refs.extend(finding.conflict_refs)
    return CREPropertyDueDiligence(
        due_diligence_id=due_diligence_id,
        opportunity_id=opportunity_id,
        property_id=property_id,
        created_at=created_at or utc_now(),
        findings=records,
        unknown_fields=list(dict.fromkeys(unknown_fields or [])),
        missing_documents=list(dict.fromkeys(missing_documents or [])),
        unresolved_items=list(dict.fromkeys(unresolved_items or [])),
        conflict_refs=list(dict.fromkeys(refs)),
        uncertainty=list(dict.fromkeys(uncertainty or [])),
        supersedes_due_diligence_id=supersedes_due_diligence_id,
    )


def validate_due_diligence_scope(
    diligence: CREPropertyDueDiligence,
    opportunity: CREOpportunityDeal,
    cre_evidence: list[CREEvidence] | None = None,
    screening: CREOpportunityScreening | None = None,
) -> None:
    """Validate identity/reference compatibility without inferring findings."""
    if diligence.opportunity_id != opportunity.opportunity_id:
        raise ValueError("due diligence opportunity_id must match the canonical opportunity")
    if diligence.property_id and opportunity.property.property_id != diligence.property_id:
        raise ValueError("due diligence property_id must match the canonical opportunity property")
    if cre_evidence is not None:
        evidence_ids = {item.evidence_id for item in cre_evidence}
        refs = {ref for finding in diligence.findings for ref in finding.evidence_refs}
        refs.update(diligence.conflict_refs)
        unknown = refs - evidence_ids
        if unknown:
            raise ValueError(f"due diligence references unknown CRE evidence: {sorted(unknown)}")
    if screening is not None and screening.opportunity_id != diligence.opportunity_id:
        raise ValueError("screening opportunity_id must match due diligence opportunity_id")
