"""Provenance-aware lender and financing information contracts.

This module represents externally supplied lender information. It does not
calculate financing consequences, select lenders, authorize capital, or
execute financing.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProvenanceType = Literal[
    "FACT", "SOURCE", "ASSUMPTION", "HYPOTHESIS", "CALCULATION",
    "INTERPRETATION", "PREDICTION", "RECOMMENDATION",
]
FreshnessStatus = Literal["CURRENT", "AGING", "STALE", "UNKNOWN"]
VerificationStatus = Literal["VERIFIED", "UNVERIFIED", "PARTIALLY_VERIFIED", "UNKNOWN"]
EvidenceStatus = Literal["OBSERVED", "ESTIMATED", "CONDITIONAL", "INCOMPLETE", "CONTRADICTORY"]
ConflictStatus = Literal["NONE", "UNRESOLVED"]


class LenderIntelligenceValidationError(ValueError):
    """Raised when lender information crosses the data-contract boundary."""


class ProvenanceRecord(BaseModel):
    """Traceability metadata for externally supplied lender information."""

    model_config = ConfigDict(extra="forbid")

    provenance: ProvenanceType = "SOURCE"
    source: str = Field(min_length=1)
    source_date: datetime | None = None
    observed_at: datetime
    review_by: datetime | None = None
    freshness_status: FreshnessStatus = "UNKNOWN"
    verification_status: VerificationStatus = "UNKNOWN"

    @model_validator(mode="after")
    def validate_dates(self) -> "ProvenanceRecord":
        if self.review_by is not None and self.review_by < self.observed_at:
            raise ValueError("review_by cannot precede observed_at")
        return self


class LenderProfile(BaseModel):
    """Descriptive identity and stated market scope for a lender."""

    model_config = ConfigDict(extra="forbid")

    lender_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    lender_type: str = Field(min_length=1)
    asset_types: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(min_length=1)


class FinancingTerms(BaseModel):
    """Externally supplied financing terms, never authoritative calculations."""

    model_config = ConfigDict(extra="forbid")

    financing_id: str = Field(min_length=1)
    lender_id: str = Field(min_length=1)
    loan_type: str = Field(min_length=1)
    minimum_loan: float | None = Field(default=None, ge=0)
    maximum_loan: float | None = Field(default=None, ge=0)
    maximum_ltv: float | None = Field(default=None, ge=0, le=1)
    maximum_ltc: float | None = Field(default=None, ge=0, le=1)
    minimum_dscr: float | None = Field(default=None, ge=0)
    minimum_debt_yield: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0, le=1)
    rate_type: str | None = None
    amortization_years: int | None = Field(default=None, gt=0, le=50)
    maturity_years: int | None = Field(default=None, gt=0, le=50)
    recourse: str | None = None
    conditions: list[str] = Field(default_factory=list)
    applicability: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus = "OBSERVED"
    provenance: list[ProvenanceRecord] = Field(min_length=1)
    unresolved_questions: list[str] = Field(default_factory=list)
    conflict_status: ConflictStatus = "NONE"
    conflicting_financing_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_structure(self) -> "FinancingTerms":
        if self.minimum_loan is not None and self.maximum_loan is not None:
            if self.minimum_loan > self.maximum_loan:
                raise ValueError("minimum_loan cannot exceed maximum_loan")
        if self.maturity_years is not None and self.amortization_years is not None:
            if self.amortization_years < self.maturity_years:
                raise ValueError("amortization_years cannot be shorter than maturity_years")
        if self.conflict_status == "UNRESOLVED" and not self.conflicting_financing_ids:
            raise ValueError("unresolved conflicts require conflicting_financing_ids")
        if self.conflict_status == "NONE" and self.conflicting_financing_ids:
            raise ValueError("conflicting_financing_ids require conflict_status=UNRESOLVED")
        return self


_CALCULATION_KEYS = {
    "dscr", "debt_service_coverage_ratio", "ltv", "loan_to_value",
    "ltc", "loan_to_cost", "debt_yield", "annual_debt_service",
    "principal_reduction", "annual_principal_reduction", "balloon_balance",
    "equity_requirement", "leveraged_cash_flow", "leveraged_cash_flows",
}


def validate_lender_evidence(inputs: list[dict]) -> None:
    """Reject authoritative financing calculations supplied as lender evidence."""
    for item in inputs:
        for key in item:
            if str(key).lower() in _CALCULATION_KEYS:
                raise LenderIntelligenceValidationError(
                    f"Authoritative financing calculations cannot be supplied as lender evidence: {key}"
                )


def validate_financing_terms_collection(terms: list[FinancingTerms]) -> None:
    """Validate collection-level conflicts without resolving them automatically."""
    ids = {term.financing_id for term in terms}
    for term in terms:
        missing = set(term.conflicting_financing_ids) - ids
        if missing:
            raise LenderIntelligenceValidationError(
                f"Unknown conflicting financing_id(s): {sorted(missing)}"
            )
