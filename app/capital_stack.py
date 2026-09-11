"""Capital stack and lender evidence research boundaries.

These models represent financing analysis and external financing research. They do
not represent lender commitments, financing authorization, or capital deployment.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


EvidenceStatus = Literal["current", "stale", "superseded", "unresolved"]
CapitalStackStatus = Literal["modeled", "incomplete", "superseded"]


class CapitalStack(BaseModel):
    """Immutable analytical representation of a proposed financing structure."""

    model_config = ConfigDict(frozen=True)

    stack_id: str = Field(min_length=1)
    created_at: datetime
    purchase_price: Optional[float] = None
    acquisition_costs: Optional[float] = None
    total_capitalization: Optional[float] = None
    debt: Optional[float] = None
    mezzanine: Optional[float] = None
    preferred_equity: Optional[float] = None
    sponsor_equity: Optional[float] = None
    other_equity: Optional[float] = None
    loan_amount: Optional[float] = None
    ltv: Optional[float] = None
    interest_rate: Optional[float] = None
    amortization_years: Optional[float] = None
    term_years: Optional[float] = None
    maturity_date: Optional[date] = None
    interest_only_years: Optional[float] = None
    dscr: Optional[float] = None
    debt_yield: Optional[float] = None
    debt_service: Optional[float] = None
    financing_fees: Optional[float] = None
    reserves: Optional[float] = None
    recourse: Optional[str] = None
    financing_assumptions: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    effective_at: Optional[datetime] = None
    uncertainty: List[str] = Field(default_factory=list)
    status: CapitalStackStatus = "modeled"
    authorization: Literal["none"] = "none"
    capital_deployment: Literal[False] = False


class LenderEvidence(BaseModel):
    """Immutable research observation about a lender or financing source."""

    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(min_length=1)
    lender_identity: str = Field(min_length=1)
    lender_type: Optional[str] = None
    asset_class_focus: List[str] = Field(default_factory=list)
    geography: List[str] = Field(default_factory=list)
    minimum_loan_size: Optional[float] = None
    maximum_loan_size: Optional[float] = None
    target_deal_size: Optional[float] = None
    ltv_range: Optional[str] = None
    dscr_requirement: Optional[str] = None
    debt_yield_requirement: Optional[str] = None
    recourse: Optional[str] = None
    interest_rate_information: Optional[str] = None
    term_information: Optional[str] = None
    amortization_information: Optional[str] = None
    financing_structure: Optional[str] = None
    source: str = Field(min_length=1)
    source_date: Optional[date] = None
    effective_at: Optional[datetime] = None
    contact_source_provenance: Optional[str] = None
    evidence_status: EvidenceStatus = "current"
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    uncertainty: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    commitment_status: Literal["research_only"] = "research_only"
    authorization: Literal["none"] = "none"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
