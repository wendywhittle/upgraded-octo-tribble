"""Canonical CRE evidence boundary.

CRE evidence preserves source observations as immutable, opportunity-scoped
artifacts. It does not create claims, assumptions, recommendations, or authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.evidence import validate_evidence


CREEvidenceStatus = Literal["observed", "sourced", "unresolved", "superseded"]
CREEvidenceCategory = Literal[
    "listing",
    "broker_statement",
    "property_record",
    "operating_statement",
    "rent_roll",
    "lease",
    "tenant",
    "market",
    "sales_comparable",
    "debt_term",
    "environmental",
    "physical_due_diligence",
    "other",
]


class CREEvidenceProvenance(BaseModel):
    """Source and temporal context retained with CRE evidence."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1)
    source_type: str | None = None
    source_reference: str | None = None
    publisher: str | None = None
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    retrieved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    point_in_time: bool = False


class CREEvidence(BaseModel):
    """Immutable, opportunity-scoped source observation."""

    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    category: CREEvidenceCategory
    subject_ref: str | None = None
    field_name: str = Field(min_length=1)
    observed_value: str | int | float | bool | None = None
    source_content: str | None = None
    observation_type: str = Field(min_length=1)
    status: CREEvidenceStatus
    provenance: CREEvidenceProvenance
    uncertainty: list[str] = Field(default_factory=list)
    freshness_seconds: float | None = Field(default=None, ge=0.0)
    validation_status: Literal["unvalidated", "verified", "blocked"] = "unvalidated"
    decision_usable: bool = False
    corroboration_refs: list[str] = Field(default_factory=list)
    dependent_evidence_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    contradictory_evidence_refs: list[str] = Field(default_factory=list)
    supersedes_evidence_id: str | None = Field(default=None, min_length=1)
    created_at: datetime
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    transaction_capability: Literal[False] = False

    @model_validator(mode="after")
    def validate_temporal_order(self) -> "CREEvidence":
        observed = self.provenance.observed_at
        retrieved = self.provenance.retrieved_at
        if observed and retrieved and retrieved < observed:
            raise ValueError("retrieved_at cannot precede observed_at")
        if observed and observed > self.created_at:
            raise ValueError("observed_at cannot be after created_at")
        if retrieved and retrieved > self.created_at:
            raise ValueError("retrieved_at cannot be after created_at")
        return self


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_cre_evidence(
    evidence: CREEvidence,
    *,
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> dict[str, Any]:
    """Reuse the generic evidence integrity gate without turning evidence into a claim.

    The adapter supplies a deterministic validation view solely for the existing
    integrity machinery. The resulting report is not stored as a claim on the
    canonical CRE evidence artifact.
    """
    validation_view = {
        "evidence_id": evidence.evidence_id,
        "source": evidence.provenance.source,
        "claim": evidence.source_content or f"{evidence.field_name}={evidence.observed_value!r}",
        "observed_at": evidence.provenance.observed_at.isoformat()
        if evidence.provenance.observed_at else None,
        "retrieved_at": evidence.provenance.retrieved_at.isoformat()
        if evidence.provenance.retrieved_at else None,
        "provenance": {
            "type": evidence.provenance.source_type or "external_source",
            "point_in_time": evidence.provenance.point_in_time,
            **evidence.provenance.metadata,
        },
    }
    return validate_evidence(validation_view, now=now, max_age_seconds=max_age_seconds)


def build_cre_evidence(
    *,
    evidence_id: str,
    opportunity_id: str,
    category: CREEvidenceCategory,
    field_name: str,
    observed_value: str | int | float | bool | None = None,
    source_content: str | None = None,
    observation_type: str = "source_observation",
    status: CREEvidenceStatus = "sourced",
    provenance: CREEvidenceProvenance,
    uncertainty: list[str] | None = None,
    freshness_seconds: float | None = None,
    validation_status: Literal["unvalidated", "verified", "blocked"] = "unvalidated",
    decision_usable: bool = False,
    corroboration_refs: list[str] | None = None,
    dependent_evidence_refs: list[str] | None = None,
    conflict_refs: list[str] | None = None,
    contradictory_evidence_refs: list[str] | None = None,
    supersedes_evidence_id: str | None = None,
    subject_ref: str | None = None,
    created_at: datetime | None = None,
) -> CREEvidence:
    """Construct canonical CRE evidence without inventing missing information."""
    return CREEvidence(
        evidence_id=evidence_id,
        opportunity_id=opportunity_id,
        category=category,
        subject_ref=subject_ref,
        field_name=field_name,
        observed_value=observed_value,
        source_content=source_content,
        observation_type=observation_type,
        status=status,
        provenance=provenance,
        uncertainty=list(dict.fromkeys(uncertainty or [])),
        freshness_seconds=freshness_seconds,
        validation_status=validation_status,
        decision_usable=decision_usable,
        corroboration_refs=list(dict.fromkeys(corroboration_refs or [])),
        dependent_evidence_refs=list(dict.fromkeys(dependent_evidence_refs or [])),
        conflict_refs=list(dict.fromkeys(conflict_refs or [])),
        contradictory_evidence_refs=list(dict.fromkeys(contradictory_evidence_refs or [])),
        supersedes_evidence_id=supersedes_evidence_id,
        created_at=created_at or utc_now(),
    )
