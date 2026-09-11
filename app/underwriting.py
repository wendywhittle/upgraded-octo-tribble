"""CRE underwriting and pro forma boundary.

A pro forma is a model of assumptions, not a statement of fact. This module
provides a typed, immutable research boundary for property/deal underwriting.
It performs no investment authorization, capital deployment, or portfolio mutation.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


UnderwritingStatus = Literal[
    "observed",
    "sourced",
    "assumed",
    "calculated",
    "projected",
    "scenario",
    "simulated",
    "unresolved",
    "superseded",
]


class UnderwritingProvenance(BaseModel):
    """Provenance for a modeled value or group of modeled values."""

    model_config = ConfigDict(frozen=True)

    source_refs: List[str] = Field(default_factory=list)
    source_date: Optional[date] = None
    effective_at: Optional[datetime] = None
    status: UnderwritingStatus
    uncertainty: List[str] = Field(default_factory=list)


class PropertyIdentity(BaseModel):
    """Minimal property identity. No inferred property facts are permitted."""

    model_config = ConfigDict(frozen=True)

    property_id: str = Field(min_length=1)
    property_type: Optional[str] = None
    address: Optional[str] = None
    market: Optional[str] = None
    units_or_sf: Optional[float] = Field(default=None, ge=0.0)
    identity_provenance: Optional[UnderwritingProvenance] = None


class AcquisitionTerms(BaseModel):
    """Acquisition inputs, explicitly separated from observed evidence."""

    model_config = ConfigDict(frozen=True)

    purchase_price: float = Field(gt=0.0)
    acquisition_costs: float = Field(default=0.0, ge=0.0)
    closing_date: Optional[date] = None
    hold_period_years: Optional[float] = Field(default=None, gt=0.0)
    provenance: UnderwritingProvenance


class OperatingAssumptions(BaseModel):
    """Operating model inputs. These are assumptions unless explicitly sourced."""

    model_config = ConfigDict(frozen=True)

    gross_revenue: Optional[float] = Field(default=None, ge=0.0)
    vacancy_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    operating_expenses: Optional[float] = Field(default=None, ge=0.0)
    capex: Optional[float] = Field(default=None, ge=0.0)
    revenue_growth_rate: Optional[float] = Field(default=None, ge=-1.0)
    expense_growth_rate: Optional[float] = Field(default=None, ge=-1.0)
    provenance: UnderwritingProvenance


class ValuationAssumptions(BaseModel):
    """Valuation inputs, never represented as observed property facts."""

    model_config = ConfigDict(frozen=True)

    exit_cap_rate: Optional[float] = Field(default=None, gt=0.0)
    discount_rate: Optional[float] = Field(default=None, gt=0.0)
    terminal_value: Optional[float] = Field(default=None, ge=0.0)
    valuation_method: Optional[str] = None
    provenance: UnderwritingProvenance


class UnderwritingFinancingReference(BaseModel):
    """Reference to financing analysis without creating a lender commitment."""

    model_config = ConfigDict(frozen=True)

    capital_stack_id: Optional[str] = None
    lender_evidence_ids: List[str] = Field(default_factory=list)
    provenance: Optional[UnderwritingProvenance] = None


class CashFlowProjection(BaseModel):
    """A dated modeled cash-flow observation or projection."""

    model_config = ConfigDict(frozen=True)

    period: int = Field(ge=0)
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    debt_service: Optional[float] = None
    net_cash_flow: Optional[float] = None
    provenance: UnderwritingProvenance


class ReturnOutputs(BaseModel):
    """Return outputs are modeled outputs, not investment facts."""

    model_config = ConfigDict(frozen=True)

    equity_multiple: Optional[float] = Field(default=None, ge=0.0)
    irr: Optional[float] = None
    cash_on_cash: Optional[float] = None
    total_profit: Optional[float] = None
    provenance: UnderwritingProvenance


class CREUnderwritingProForma(BaseModel):
    """Smallest coherent CRE underwriting/pro forma boundary."""

    model_config = ConfigDict(frozen=True)

    underwriting_id: str = Field(min_length=1)
    opportunity_id: Optional[str] = Field(default=None, min_length=1)
    created_at: datetime
    property: PropertyIdentity
    acquisition: AcquisitionTerms
    operations: OperatingAssumptions
    valuation: ValuationAssumptions
    financing: UnderwritingFinancingReference = Field(default_factory=UnderwritingFinancingReference)
    cash_flows: List[CashFlowProjection] = Field(default_factory=list)
    returns: Optional[ReturnOutputs] = None
    assumptions: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    uncertainty: List[str] = Field(default_factory=list)
    status: UnderwritingStatus = "projected"
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False

    @model_validator(mode="after")
    def enforce_model_boundary(self) -> "CREUnderwritingProForma":
        if self.status in {"observed", "sourced"} and self.assumptions:
            raise ValueError("Observed/sourced underwriting artifacts cannot contain modeled assumptions as facts")
        return self


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_cre_underwriting(
    *,
    underwriting_id: str,
    property: PropertyIdentity,
    acquisition: AcquisitionTerms,
    operations: OperatingAssumptions,
    valuation: ValuationAssumptions,
    financing: UnderwritingFinancingReference | None = None,
    cash_flows: List[CashFlowProjection] | None = None,
    returns: ReturnOutputs | None = None,
    assumptions: List[str] | None = None,
    source_refs: List[str] | None = None,
    uncertainty: List[str] | None = None,
    status: UnderwritingStatus = "projected",
    opportunity_id: str | None = None,
    created_at: datetime | None = None,
) -> CREUnderwritingProForma:
    """Construct an immutable underwriting artifact without inventing missing data."""
    return CREUnderwritingProForma(
        underwriting_id=underwriting_id,
        opportunity_id=opportunity_id,
        created_at=created_at or utc_now(),
        property=property,
        acquisition=acquisition,
        operations=operations,
        valuation=valuation,
        financing=financing or UnderwritingFinancingReference(),
        cash_flows=list(cash_flows or []),
        returns=returns,
        assumptions=list(dict.fromkeys(assumptions or [])),
        source_refs=list(dict.fromkeys(source_refs or [])),
        uncertainty=list(dict.fromkeys(uncertainty or [])),
        status=status,
    )
