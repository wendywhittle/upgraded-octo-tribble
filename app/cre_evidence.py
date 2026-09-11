"""Canonical CRE evidence boundary.

CRE evidence is immutable, opportunity-scoped source material or observation.
It is not a claim, assumption, recommendation, authorization, or transaction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.evidence import validate_evidence

CREEvidenceStatus = Literal["observed", "sourced", "unresolved", "superseded"]
CREEvidenceCategory = Literal[
    "listing", "broker_statement", "property_record", "operating_statement",
    "rent_roll", "lease", "tenant", "market", "sales_comparable", "debt_term",
    "environmental", "physical_due_diligence", "other"
]


class CREEvidenceProvenance(BaseModel):
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
    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    category: CREEvidenceCategory
    subject_ref: str | None = None
    field_name: str = Field(min_length=1)
    observed_value: str | int | float | bool | None = None
    source_content: str | None = None
    observation_type: str = Field(min_length=1)
    status: CREEvidenceStatus = "sourced"
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
    """Apply the existing generic evidence integrity gate to CRE evidence."""
    view = {
        "evidence_id": evidence.evidence_id,
        "source": evidence.provenance.source,
        "claim": evidence.source_content or f"{evidence.field_name}={evidence.observed_value!r}",
        "observed_at": evidence.provenance.observed_at.isoformat() if evidence.provenance.observed_at else None,
        "retrieved_at": evidence.provenance.retrieved_at.isoformat() if evidence.provenance.retrieved_at else None,
        "provenance": {
            "type": evidence.provenance.source_type or "external_source",
            "point_in_time": evidence.provenance.point_in_time,
            **evidence.provenance.metadata,
        },
    }
    return validate_evidence(view, now=now, max_age_seconds=max_age_seconds)


def build_cre_evidence(**kwargs: Any) -> CREEvidence:
    """Construct an immutable CRE evidence record without inference."""
    kwargs.setdefault("created_at", utc_now())
    for key in (
        "uncertainty", "corroboration_refs", "dependent_evidence_refs",
        "conflict_refs", "contradictory_evidence_refs",
    ):
        kwargs[key] = list(dict.fromkeys(kwargs.get(key) or []))
    return CREEvidence(**kwargs)
