"""Deterministic CRE pro forma engine.

This module is deliberately independent of agents, simulation, and investment
approval. It calculates asset economics from validated underwriting inputs.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, model_validator


class ProFormaValidationError(ValueError):
    """Raised when a CRE pro forma contains invalid or incomplete inputs."""


class ProFormaInput(BaseModel):
    asset_id: str
    acquisition_price: float = Field(gt=0)
    acquisition_costs: float = Field(default=0.0, ge=0)
    projection_years: int = Field(default=5, ge=1, le=50)
    annual_rent: float = Field(gt=0)
    other_income: float = Field(default=0.0, ge=0)
    initial_occupancy: float = Field(ge=0, le=1)
    rent_growth: float = Field(default=0.0, ge=-1)
    vacancy_rate: float = Field(default=0.0, ge=0, le=1)
    operating_expenses: float = Field(ge=0)
    expense_growth: float = Field(default=0.0, ge=-1)
    management_expense: float = Field(default=0.0, ge=0)
    property_tax: float = Field(default=0.0, ge=0)
    insurance: float = Field(default=0.0, ge=0)
    maintenance: float = Field(default=0.0, ge=0)
    utilities: float = Field(default=0.0, ge=0)
    capex: float = Field(default=0.0, ge=0)
    reserves: float = Field(default=0.0, ge=0)
    tenant_improvements: float = Field(default=0.0, ge=0)
    leasing_commissions: float = Field(default=0.0, ge=0)
    entry_cap_rate: float = Field(gt=0)
    exit_cap_rate: float = Field(gt=0)
    exit_costs: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_occupancy(self) -> "ProFormaInput":
        if self.initial_occupancy + self.vacancy_rate > 1:
            raise ValueError("initial_occupancy plus vacancy_rate cannot exceed 1")
        return self


class AnnualProForma(BaseModel):
    year: int
    potential_rent: float
    effective_rent: float
    other_income: float
    effective_gross_income: float
    operating_expenses: float
    noi: float
    noi_margin: float
    capex: float
    reserves: float
    tenant_improvements: float
    leasing_commissions: float
    property_cash_flow: float


class ProFormaResult(BaseModel):
    engine: str = "AletheiaTelos Deterministic CRE Pro Forma Engine v1"
    asset_id: str
    acquisition_price: float
    acquisition_costs: float
    acquisition_basis: float
    entry_valuation: float
    exit_valuation: float
    terminal_value: float
    exit_costs: float
    annual: List[AnnualProForma]
    unlevered_cash_flows: List[float]
    unlevered_irr: float | None
    unlevered_equity_multiple: float
    output_types: dict[str, str] = Field(default_factory=lambda: {
        "noi": "CALCULATION",
        "property_cash_flow": "CALCULATION",
        "entry_valuation": "CALCULATION",
        "exit_valuation": "CALCULATION",
        "unlevered_irr": "CALCULATION",
        "unlevered_equity_multiple": "CALCULATION",
    })


def calculate_proforma(inputs: ProFormaInput) -> ProFormaResult:
    """Calculate a reproducible unlevered CRE pro forma."""
    basis = inputs.acquisition_price + inputs.acquisition_costs
    annual: list[AnnualProForma] = []

    for year in range(1, inputs.projection_years + 1):
        growth_factor = (1 + inputs.rent_growth) ** (year - 1)
        expense_factor = (1 + inputs.expense_growth) ** (year - 1)
        potential_rent = inputs.annual_rent * growth_factor
        effective_occupancy = inputs.initial_occupancy * (1 - inputs.vacancy_rate)
        effective_rent = potential_rent * effective_occupancy
        other_income = inputs.other_income * growth_factor
        egi = effective_rent + other_income
        expenses = (
            inputs.operating_expenses + inputs.management_expense + inputs.property_tax
            + inputs.insurance + inputs.maintenance + inputs.utilities
        ) * expense_factor
        noi = egi - expenses
        annual_capex = (inputs.capex + inputs.reserves + inputs.tenant_improvements + inputs.leasing_commissions) * expense_factor
        pcf = noi - annual_capex
        margin = noi / egi if egi else 0.0
        annual.append(AnnualProForma(
            year=year,
            potential_rent=round(potential_rent, 2),
            effective_rent=round(effective_rent, 2),
            other_income=round(other_income, 2),
            effective_gross_income=round(egi, 2),
            operating_expenses=round(expenses, 2),
            noi=round(noi, 2),
            noi_margin=round(margin, 6),
            capex=round(inputs.capex * expense_factor, 2),
            reserves=round(inputs.reserves * expense_factor, 2),
            tenant_improvements=round(inputs.tenant_improvements * expense_factor, 2),
            leasing_commissions=round(inputs.leasing_commissions * expense_factor, 2),
            property_cash_flow=round(pcf, 2),
        ))

    entry_valuation = annual[0].noi / inputs.entry_cap_rate
    exit_valuation = annual[-1].noi / inputs.exit_cap_rate
    terminal_value = exit_valuation
    exit_costs = inputs.exit_costs
    unlevered_cash_flows = [-basis] + [row.property_cash_flow for row in annual]
    unlevered_cash_flows[-1] += terminal_value - exit_costs
    irr = _irr(unlevered_cash_flows)
    positive_cash = sum(cf for cf in unlevered_cash_flows[1:] if cf > 0)

    return ProFormaResult(
        asset_id=inputs.asset_id,
        acquisition_price=inputs.acquisition_price,
        acquisition_costs=inputs.acquisition_costs,
        acquisition_basis=round(basis, 2),
        entry_valuation=round(entry_valuation, 2),
        exit_valuation=round(exit_valuation, 2),
        terminal_value=round(terminal_value, 2),
        exit_costs=round(exit_costs, 2),
        annual=annual,
        unlevered_cash_flows=[round(x, 2) for x in unlevered_cash_flows],
        unlevered_irr=round(irr, 10) if irr is not None else None,
        unlevered_equity_multiple=round(positive_cash / basis, 10),
    )


def _npv(rate: float, cash_flows: list[float]) -> float:
    return sum(cf / ((1 + rate) ** period) for period, cf in enumerate(cash_flows))


def _irr(cash_flows: list[float]) -> float | None:
    if not cash_flows or not (any(x > 0 for x in cash_flows) and any(x < 0 for x in cash_flows)):
        return None
    low, high = -0.999999, 10.0
    f_low, f_high = _npv(low, cash_flows), _npv(high, cash_flows)
    while f_low * f_high > 0 and high < 1000:
        high *= 2
        f_high = _npv(high, cash_flows)
    if f_low * f_high > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2
        f_mid = _npv(mid, cash_flows)
        if abs(f_mid) < 1e-10:
            return mid
        if f_low * f_mid <= 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2
