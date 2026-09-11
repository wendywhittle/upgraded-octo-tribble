"""Canonical CRE opportunity/deal representation.

A CRE opportunity is an object of analysis, not an authorization to act.  This
module preserves the distinction between property identity, observed deal data,
evidence, uncertainty, and later analytical assumptions.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OpportunityStatus = Literal[
    "observed",
    "sourced",
    "assumed",
    "unresolved",
    "superseded",
]

ObservationCategory = Literal[
    "deal_term",
    "operating",
    "tenancy",
    "physical",
    "market",
    "other",
]


class OpportunityProvenance(BaseModel):
    """Source and temporal context for an opportunity observation."""

    model_config = ConfigDict(frozen=True)

    source_refs: list[str] = Field(default_factory=list)
    source_type: str | None = None
    source_reference: str | None = None
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    status: OpportunityStatus
    uncertainty: list[str] = Field(default_factory=list)


class PropertyIdentityReference(BaseModel):
    """Minimal property identity/reference without underwriting assumptions."""

    model_config = ConfigDict(frozen=True)

    property_id: str = Field(min_length=1)
    property_type: str | None = None
    address: str | None = None
    market: str | None = None
    units_or_sf: float | None = Field(default=None, ge=0.0)
    provenance: OpportunityProvenance | None = None


class CREOpportunityObservation(BaseModel):
    """One observed/sourced opportunity datum with explicit epistemic status."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(min_length=1)
    category: ObservationCategory
    field_name: str = Field(min_length=1)
    value: str | int | float | bool | None = None
    status: OpportunityStatus
    provenance: OpportunityProvenance
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)


class CREOpportunityDeal(BaseModel):
    """Canonical immutable representation of a real-world CRE opportunity."""

    model_config = ConfigDict(frozen=True)

    opportunity_id: str = Field(min_length=1)
    property: PropertyIdentityReference
    source_type: str | None = None
    source_reference: str | None = None
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    status: OpportunityStatus = "observed"
    observations: list[CREOpportunityObservation] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    unknown_fields: list[str] = Field(default_factory=list)
    unresolved_fields: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    supersedes_opportunity_id: str | None = None
    created_at: datetime
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    authorization_capability: Literal[False] = False


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def build_cre_opportunity(
    *,
    opportunity_id: str,
    property: PropertyIdentityReference,
    observations: list[CREOpportunityObservation] | None = None,
    source_type: str | None = None,
    source_reference: str | None = None,
    observed_at: datetime | None = None,
    effective_at: datetime | None = None,
    status: OpportunityStatus = "observed",
    evidence_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    unknown_fields: list[str] | None = None,
    unresolved_fields: list[str] | None = None,
    conflict_refs: list[str] | None = None,
    uncertainty: list[str] | None = None,
    supersedes_opportunity_id: str | None = None,
    created_at: datetime | None = None,
) -> CREOpportunityDeal:
    """Construct an immutable opportunity without inventing missing information."""
    records = list(observations or [])
    return CREOpportunityDeal(
        opportunity_id=opportunity_id,
        property=property,
        source_type=source_type,
        source_reference=source_reference,
        observed_at=observed_at,
        effective_at=effective_at,
        status=status,
        observations=records,
        evidence_refs=list(dict.fromkeys(evidence_refs or [])),
        source_refs=list(dict.fromkeys(source_refs or [])),
        unknown_fields=list(dict.fromkeys(unknown_fields or [])),
        unresolved_fields=list(dict.fromkeys(unresolved_fields or [])),
        conflict_refs=list(dict.fromkeys(conflict_refs or [])),
        uncertainty=list(dict.fromkeys(uncertainty or [])),
        supersedes_opportunity_id=supersedes_opportunity_id,
        created_at=created_at or utc_now(),
    )
