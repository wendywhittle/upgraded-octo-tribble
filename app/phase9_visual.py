"""Visual integration boundary for the Phase 9 Investment Case Assembly.

This module adapts browser-safe request data into the existing deterministic
Phase 9 assembly. It does not authorize, mutate workflow state, select lenders,
or perform execution.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.capital_stack import CapitalSource, CapitalStack, CapitalUse, DebtTerms
from app.investment_case_assembly import assemble_investment_case
from app.proforma import ProFormaInput
from app.cre_simulation import CRESimulationConfig


class Phase9VisualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1)
    acquisition_price: float = Field(gt=0)
    acquisition_costs: float = Field(default=0, ge=0)
    annual_rent: float = Field(gt=0)
    other_income: float = Field(default=0, ge=0)
    initial_occupancy: float = Field(ge=0, le=1)
    rent_growth: float = Field(default=0, ge=-1)
    vacancy_rate: float = Field(default=0, ge=0, le=1)
    operating_expenses: float = Field(ge=0)
    expense_growth: float = Field(default=0, ge=-1)
    management_expense: float = Field(default=0, ge=0)
    property_tax: float = Field(default=0, ge=0)
    insurance: float = Field(default=0, ge=0)
    maintenance: float = Field(default=0, ge=0)
    utilities: float = Field(default=0, ge=0)
    capex: float = Field(default=0, ge=0)
    reserves: float = Field(default=0, ge=0)
    tenant_improvements: float = Field(default=0, ge=0)
    leasing_commissions: float = Field(default=0, ge=0)
    entry_cap_rate: float = Field(gt=0)
    exit_cap_rate: float = Field(gt=0)
    exit_costs: float = Field(default=0, ge=0)
    debt_amount: float = Field(default=0, ge=0)
    interest_rate: float = Field(default=0, ge=0, le=1)
    amortization_years: int = Field(default=25, ge=1, le=50)
    maturity_years: int = Field(default=10, ge=1, le=50)
    equity_contribution: float = Field(gt=0)
    simulation_paths: int = Field(default=5000, ge=100, le=100000)
    simulation_seed: int = 42


def assemble_visual_case(request: Phase9VisualRequest) -> dict[str, Any]:
    """Run the existing Phase 9 engines and return JSON-safe presentation data."""
    proforma_input = ProFormaInput(**request.model_dump(exclude={"debt_amount", "interest_rate", "amortization_years", "maturity_years", "equity_contribution", "simulation_paths", "simulation_seed"}))

    uses = [
        CapitalUse(name="Acquisition", use_type="ACQUISITION", amount=request.acquisition_price),
        CapitalUse(name="Acquisition Costs", use_type="ACQUISITION_COSTS", amount=request.acquisition_costs),
    ]
    sources = []
    if request.debt_amount > 0:
        sources.append(CapitalSource(
            name="Proposed Debt",
            source_type="DEBT",
            amount=request.debt_amount,
            provenance="ASSUMPTION",
            debt_terms=DebtTerms(
                interest_rate=request.interest_rate,
                amortization_years=request.amortization_years,
                maturity_years=request.maturity_years,
            ),
        ))
    sources.append(CapitalSource(
        name="Equity",
        source_type="EQUITY",
        amount=request.equity_contribution,
        provenance="ASSUMPTION",
    ))
    stack = CapitalStack(sources=sources, uses=uses)

    assembly = assemble_investment_case(
        case_identity=request.asset_id,
        proforma_input=proforma_input,
        simulation_config=CRESimulationConfig(paths=request.simulation_paths, seed=request.simulation_seed),
        capital_stack=stack,
        lender_profiles=(),
        lender_terms=(),
        evidence=(),
        agent_perspectives=(),
        disagreements=(),
        investment_thesis=None,
    )

    return {
        "assembly": assembly.model_dump(mode="json"),
        "governance": {
            "human_authorization_required": True,
            "authorization_created": False,
            "workflow_mutated": False,
            "portfolio_created": False,
            "transaction_executed": False,
            "lender_selection_performed": False,
            "lender_evidence_provided": False,
        },
        "visual_integration": {
            "pipeline": [
                "DEAL", "PRO_FORMA", "SCENARIOS", "SIMULATION", "CONTRARIAN",
                "CAPITAL_STACK", "LENDER_EVIDENCE", "INVESTMENT_SYNTHESIS",
                "STRUCTURED_INVESTMENT_CASE", "HUMAN_DECISION_GATE",
            ],
            "lender_evidence_status": "UNKNOWN / NOT PROVIDED",
            "authoritative_calculations": "EXISTING_PYTHON_ENGINES",
        },
    }
