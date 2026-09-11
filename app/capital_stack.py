"""Deterministic CRE capital stack and financing analysis.

This module consumes authoritative operating outputs and calculates financing
consequences. It does not authorize financing, mutate workflow state, or
execute transactions.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.proforma import ProFormaResult

ProvenanceType = Literal[
    "FACT", "SOURCE", "ASSUMPTION", "HYPOTHESIS", "CALCULATION",
    "INTERPRETATION", "PREDICTION", "RECOMMENDATION",
]


class CapitalStackValidationError(ValueError):
    """Raised when a capital structure is invalid or cannot be reconciled."""


class DebtTerms(BaseModel):
    """Terms for a fixed-rate, fully amortizing loan with a defined maturity."""

    model_config = ConfigDict(extra="forbid")

    interest_rate: float = Field(ge=0, le=1)
    amortization_years: int = Field(gt=0, le=50)
    maturity_years: int = Field(gt=0, le=50)


class CapitalSource(BaseModel):
    """A proposed source of capital; debt terms are required for debt sources."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    amount: float = Field(gt=0)
    provenance: ProvenanceType = "ASSUMPTION"
    debt_terms: DebtTerms | None = None

    @model_validator(mode="after")
    def validate_debt_terms(self) -> "CapitalSource":
        is_debt = "DEBT" in self.source_type.upper()
        if is_debt and self.debt_terms is None:
            raise ValueError("Debt sources require debt_terms")
        if not is_debt and self.debt_terms is not None:
            raise ValueError("Debt terms may only be supplied for debt sources")
        return self


class CapitalUse(BaseModel):
    """An explicit use of capital in the proposed transaction."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    use_type: str = Field(min_length=1)
    amount: float = Field(gt=0)
    provenance: ProvenanceType = "ASSUMPTION"


class CapitalStack(BaseModel):
    """Validated sources-and-uses representation."""

    model_config = ConfigDict(extra="forbid")

    sources: list[CapitalSource] = Field(min_length=1)
    uses: list[CapitalUse] = Field(min_length=1)

    @property
    def total_sources(self) -> float:
        return round(sum(source.amount for source in self.sources), 2)

    @property
    def total_uses(self) -> float:
        return round(sum(use.amount for use in self.uses), 2)

    @property
    def variance(self) -> float:
        return round(self.total_sources - self.total_uses, 2)

    @property
    def balanced(self) -> bool:
        return abs(self.variance) < 0.005


class DebtAnalysis(BaseModel):
    """Calculated consequences for one debt source."""

    model_config = ConfigDict(extra="forbid")

    source_name: str
    loan_amount: float
    interest_rate: float
    amortization_years: int
    maturity_years: int
    annual_debt_service: float
    annual_principal_reduction: list[float]
    balloon_balance: float
    output_types: Dict[str, str] = Field(default_factory=lambda: {
        "loan_amount": "CALCULATION",
        "annual_debt_service": "CALCULATION",
        "annual_principal_reduction": "CALCULATION",
        "balloon_balance": "CALCULATION",
    })


class FinancingAnalysis(BaseModel):
    """Deterministic financing consequences for a validated capital stack."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str
    total_sources: float
    total_uses: float
    sources_uses_variance: float
    balanced: bool
    total_debt: float
    equity_requirement: float
    property_value: float
    loan_to_value: float | None
    loan_to_cost: float | None
    annual_debt_service: float
    debt_service_coverage_ratio: float | None
    debt_yield: float | None
    debt_analyses: list[DebtAnalysis]
    leveraged_cash_flows: list[float]
    provenance: Dict[str, Any]
    output_types: Dict[str, str] = Field(default_factory=lambda: {
        "total_sources": "CALCULATION",
        "total_uses": "CALCULATION",
        "sources_uses_variance": "CALCULATION",
        "balanced": "CALCULATION",
        "total_debt": "CALCULATION",
        "equity_requirement": "CALCULATION",
        "loan_to_value": "CALCULATION",
        "loan_to_cost": "CALCULATION",
        "annual_debt_service": "CALCULATION",
        "debt_service_coverage_ratio": "CALCULATION",
        "debt_yield": "CALCULATION",
        "leveraged_cash_flows": "CALCULATION",
    })


def _annual_debt_service(principal: float, annual_rate: float, amortization_years: int) -> float:
    if annual_rate == 0:
        return principal / amortization_years
    payment = principal * annual_rate / (1 - (1 + annual_rate) ** (-amortization_years))
    return payment


def _loan_schedule(principal: float, terms: DebtTerms) -> tuple[float, list[float], float]:
    payment = _annual_debt_service(principal, terms.interest_rate, terms.amortization_years)
    balance = principal
    reductions: list[float] = []
    for _year in range(1, terms.maturity_years + 1):
        interest = balance * terms.interest_rate
        principal_reduction = min(max(payment - interest, 0.0), balance)
        reductions.append(round(principal_reduction, 2))
        balance = max(balance - principal_reduction, 0.0)
    return round(payment, 2), reductions, round(balance, 2)


def analyze_capital_stack(
    stack: CapitalStack,
    *,
    proforma: ProFormaResult,
    property_value: float | None = None,
) -> FinancingAnalysis:
    """Calculate financing consequences without recalculating operating economics."""
    if not stack.balanced:
        raise CapitalStackValidationError(
            f"Sources and uses do not reconcile: variance={stack.variance:.2f}"
        )
    if property_value is not None and property_value <= 0:
        raise CapitalStackValidationError("property_value must be positive")

    total_sources = stack.total_sources
    total_uses = stack.total_uses
    debt_sources = [source for source in stack.sources if "DEBT" in source.source_type.upper()]
    total_debt = round(sum(source.amount for source in debt_sources), 2)
    equity_requirement = round(total_uses - total_debt, 2)
    value = property_value if property_value is not None else proforma.entry_valuation
    annual_debt_service = 0.0
    debt_analyses: list[DebtAnalysis] = []

    for source in debt_sources:
        assert source.debt_terms is not None
        payment, reductions, balloon = _loan_schedule(source.amount, source.debt_terms)
        annual_debt_service += payment
        debt_analyses.append(DebtAnalysis(
            source_name=source.name,
            loan_amount=round(source.amount, 2),
            interest_rate=source.debt_terms.interest_rate,
            amortization_years=source.debt_terms.amortization_years,
            maturity_years=source.debt_terms.maturity_years,
            annual_debt_service=payment,
            annual_principal_reduction=reductions,
            balloon_balance=balloon,
        ))

    annual_debt_service = round(annual_debt_service, 2)
    first_year_noi = proforma.annual[0].noi if proforma.annual else None
    dscr = round(first_year_noi / annual_debt_service, 10) if first_year_noi is not None and annual_debt_service > 0 else None
    debt_yield = round(first_year_noi / total_debt, 10) if first_year_noi is not None and total_debt > 0 else None
    ltv = round(total_debt / value, 10) if value > 0 else None
    ltc = round(total_debt / total_uses, 10) if total_uses > 0 else None
    leveraged_cash_flows = [
        round(cf - annual_debt_service, 2) for cf in proforma.unlevered_cash_flows[1:]
    ]

    return FinancingAnalysis(
        asset_id=proforma.asset_id,
        total_sources=total_sources,
        total_uses=total_uses,
        sources_uses_variance=stack.variance,
        balanced=stack.balanced,
        total_debt=total_debt,
        equity_requirement=equity_requirement,
        property_value=round(value, 2),
        loan_to_value=ltv,
        loan_to_cost=ltc,
        annual_debt_service=annual_debt_service,
        debt_service_coverage_ratio=dscr,
        debt_yield=debt_yield,
        debt_analyses=debt_analyses,
        leveraged_cash_flows=leveraged_cash_flows,
        provenance={
            "capital_stack_terms": "SOURCE_OR_ASSUMPTION",
            "operating_cash_flow": "CALCULATION",
            "financing_metrics": "CALCULATION",
            "authority": "CAPITAL_STACK_ANALYSIS_ONLY",
        },
    )


def validate_financing_provenance(inputs: Iterable[Dict[str, Any]]) -> None:
    """Reject agent-style calculated metrics from becoming authoritative inputs."""
    calculated = {
        "dscr", "debt_service_coverage_ratio", "ltv", "loan_to_value", "ltc",
        "loan_to_cost", "debt_yield", "annual_debt_service", "balloon_balance",
    }
    for item in inputs:
        for key in item:
            if str(key).lower() in calculated:
                raise CapitalStackValidationError(
                    f"Authoritative financing calculations cannot be supplied as inputs: {key}"
                )
