"""Deterministic CRE scenario analysis boundary.

Scenario analysis varies explicit underwriting inputs and reuses the existing
calculation engine. It does not forecast scenario likelihood, simulate
uncertainty, recommend investments, authorize action, or mutate underwriting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.underwriting import CREUnderwritingProForma
from app.underwriting_calculations import (
    CalculationResult,
    annual_debt_service,
    cap_rate,
    cash_flow_after_debt_service,
    cash_on_cash,
    dscr,
    effective_gross_income,
    implied_value,
    loan_amount,
    ltv,
    net_operating_income,
)

ScenarioType = Literal["base", "upside", "downside", "stress", "adversarial"]
ScenarioStatus = Literal["scenario", "unresolved", "superseded"]

# These are deliberately limited to inputs accepted by the existing deterministic
# calculation functions. Underwriting fields such as vacancy_rate are not silently
# transformed into vacancy_credit_loss because that would introduce new financial logic.
ScenarioInputName = Literal[
    "gross_potential_income",
    "vacancy_credit_loss",
    "operating_expenses",
    "property_value",
    "cap_rate",
    "loan_amount",
    "ltv",
    "principal",
    "annual_interest_rate",
    "amortization_years",
    "equity_invested",
]


class ScenarioOverride(BaseModel):
    """One explicit calculation-input override."""

    model_config = ConfigDict(frozen=True)

    input_name: ScenarioInputName
    value: float


class ScenarioProvenance(BaseModel):
    """Reconstruction metadata for one scenario artifact."""

    model_config = ConfigDict(frozen=True)

    base_underwriting_id: str = Field(min_length=1)
    base_underwriting_ref: str = Field(min_length=1)
    override_refs: tuple[str, ...] = ()
    calculation_refs: tuple[str, ...] = ()
    formula_version: str = "cre-underwriting-v1"
    created_at: datetime


class ScenarioInputSet(BaseModel):
    """Resolved scenario inputs, preserving missing values as missing."""

    model_config = ConfigDict(frozen=True)

    gross_potential_income: float | None = None
    vacancy_credit_loss: float | None = None
    operating_expenses: float | None = None
    property_value: float | None = None
    cap_rate: float | None = None
    loan_amount: float | None = None
    ltv: float | None = None
    principal: float | None = None
    annual_interest_rate: float | None = None
    amortization_years: float | None = None
    equity_invested: float | None = None


class CREScenarioAnalysis(BaseModel):
    """Immutable deterministic scenario definition and calculated outputs."""

    model_config = ConfigDict(frozen=True)

    scenario_id: str = Field(min_length=1)
    scenario_name: str = Field(min_length=1)
    scenario_type: ScenarioType
    status: ScenarioStatus = "scenario"
    base_underwriting_id: str = Field(min_length=1)
    base_underwriting_ref: str = Field(min_length=1)
    overrides: tuple[ScenarioOverride, ...] = ()
    inputs: ScenarioInputSet
    calculations: tuple[CalculationResult, ...] = ()
    provenance: ScenarioProvenance
    uncertainty: tuple[str, ...] = ()
    supersedes_scenario_id: str | None = None
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    transaction_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    authorization_capability: Literal[False] = False


class ScenarioMetricComparison(BaseModel):
    """Descriptive metric values across scenarios. No ranking or recommendation."""

    model_config = ConfigDict(frozen=True)

    calculation_type: str = Field(min_length=1)
    scenario_values: tuple[tuple[str, float | None], ...]


class ScenarioComparison(BaseModel):
    """Immutable descriptive comparison of scenario outputs."""

    model_config = ConfigDict(frozen=True)

    comparison_id: str = Field(min_length=1)
    scenario_ids: tuple[str, ...] = ()
    metrics: tuple[ScenarioMetricComparison, ...] = ()
    created_at: datetime
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    transaction_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    authorization_capability: Literal[False] = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _base_inputs(underwriting: CREUnderwritingProForma) -> ScenarioInputSet:
    """Map only directly compatible underwriting fields into calculation inputs."""
    return ScenarioInputSet(
        gross_potential_income=underwriting.operations.gross_revenue,
        operating_expenses=underwriting.operations.operating_expenses,
        property_value=underwriting.acquisition.purchase_price,
    )


def _apply_overrides(base: ScenarioInputSet, overrides: tuple[ScenarioOverride, ...]) -> ScenarioInputSet:
    values = base.model_dump()
    for override in overrides:
        values[override.input_name] = override.value
    return ScenarioInputSet(**values)


def _validate_overrides(overrides: tuple[ScenarioOverride, ...]) -> None:
    names = [item.input_name for item in overrides]
    if len(names) != len(set(names)):
        raise ValueError("Each scenario input may be overridden at most once")


def _calculate(inputs: ScenarioInputSet, scenario_ref: str) -> tuple[CalculationResult, ...]:
    """Invoke existing calculation functions only; never duplicate their formulas."""
    results: list[CalculationResult] = []
    refs = (scenario_ref,)

    if inputs.gross_potential_income is not None and inputs.vacancy_credit_loss is not None:
        egi = effective_gross_income(inputs.gross_potential_income, inputs.vacancy_credit_loss, input_refs=refs)
    else:
        missing = tuple(name for name, value in (
            ("gross_potential_income", inputs.gross_potential_income),
            ("vacancy_credit_loss", inputs.vacancy_credit_loss),
        ) if value is None)
        egi = CalculationResult(
            calculation_type="effective_gross_income",
            status="unresolved",
            missing_inputs=missing,
            input_refs=refs,
        )
    results.append(egi)

    if egi.value is not None and inputs.operating_expenses is not None:
        noi = net_operating_income(egi.value, inputs.operating_expenses, input_refs=refs)
    else:
        missing = tuple(name for name, value in (
            ("effective_gross_income", egi.value),
            ("operating_expenses", inputs.operating_expenses),
        ) if value is None)
        noi = CalculationResult(
            calculation_type="net_operating_income",
            status="unresolved",
            missing_inputs=missing,
            input_refs=refs,
        )
    results.append(noi)

    if noi.value is not None and inputs.property_value is not None:
        results.append(cap_rate(noi.value, inputs.property_value, input_refs=refs))
    else:
        results.append(CalculationResult(
            calculation_type="cap_rate",
            status="unresolved",
            missing_inputs=tuple(name for name, value in (("noi", noi.value), ("property_value", inputs.property_value)) if value is None),
            input_refs=refs,
        ))

    if noi.value is not None and inputs.cap_rate is not None:
        results.append(implied_value(noi.value, inputs.cap_rate, input_refs=refs))

    if inputs.property_value is not None and inputs.ltv is not None:
        results.append(loan_amount(inputs.property_value, inputs.ltv, input_refs=refs))

    if inputs.loan_amount is not None and inputs.property_value is not None:
        results.append(ltv(inputs.loan_amount, inputs.property_value, input_refs=refs))

    if inputs.principal is not None and inputs.annual_interest_rate is not None and inputs.amortization_years is not None:
        results.append(annual_debt_service(
            inputs.principal,
            inputs.annual_interest_rate,
            int(inputs.amortization_years),
            input_refs=refs,
        ))

    debt = next((item for item in results if item.calculation_type == "annual_debt_service" and item.value is not None), None)
    if noi.value is not None and debt is not None:
        results.append(dscr(noi.value, debt.value, input_refs=refs))
        results.append(cash_flow_after_debt_service(noi.value, debt.value, input_refs=refs))

    cash_flow = next((item for item in results if item.calculation_type == "cash_flow_after_debt_service" and item.value is not None), None)
    if cash_flow is not None and inputs.equity_invested is not None:
        results.append(cash_on_cash(cash_flow.value, inputs.equity_invested, input_refs=refs))

    return tuple(results)


def build_cre_scenario(
    *,
    scenario_id: str,
    scenario_name: str,
    scenario_type: ScenarioType,
    underwriting: CREUnderwritingProForma,
    overrides: tuple[ScenarioOverride, ...] = (),
    uncertainty: tuple[str, ...] = (),
    supersedes_scenario_id: str | None = None,
    created_at: datetime | None = None,
) -> CREScenarioAnalysis:
    """Build a new scenario without mutating the source underwriting."""
    _validate_overrides(overrides)
    now = created_at or utc_now()
    inputs = _apply_overrides(_base_inputs(underwriting), overrides)
    calculations = _calculate(inputs, f"scenario:{scenario_id}")
    calculation_refs = tuple(f"calculation:{scenario_id}:{item.calculation_type}" for item in calculations)
    provenance = ScenarioProvenance(
        base_underwriting_id=underwriting.underwriting_id,
        base_underwriting_ref=f"underwriting:{underwriting.underwriting_id}",
        override_refs=tuple(f"override:{scenario_id}:{item.input_name}" for item in overrides),
        calculation_refs=calculation_refs,
        created_at=now,
    )
    return CREScenarioAnalysis(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        scenario_type=scenario_type,
        status="scenario" if all(item.status == "calculated" for item in calculations if item.calculation_type in {"effective_gross_income", "net_operating_income"}) else "unresolved",
        base_underwriting_id=underwriting.underwriting_id,
        base_underwriting_ref=provenance.base_underwriting_ref,
        overrides=overrides,
        inputs=inputs,
        calculations=calculations,
        provenance=provenance,
        uncertainty=uncertainty,
        supersedes_scenario_id=supersedes_scenario_id,
    )


def compare_scenarios(
    scenarios: tuple[CREScenarioAnalysis, ...],
    *,
    comparison_id: str,
    calculation_types: tuple[str, ...] = (),
    created_at: datetime | None = None,
) -> ScenarioComparison:
    """Produce a descriptive comparison without ranking scenarios or recommending action."""
    selected = calculation_types or tuple(dict.fromkeys(
        calculation.calculation_type
        for scenario in scenarios
        for calculation in scenario.calculations
    ))
    metrics: list[ScenarioMetricComparison] = []
    for calculation_type in selected:
        values = []
        for scenario in scenarios:
            result = next((item for item in scenario.calculations if item.calculation_type == calculation_type), None)
            values.append((scenario.scenario_id, result.value if result else None))
        metrics.append(ScenarioMetricComparison(calculation_type=calculation_type, scenario_values=tuple(values)))
    return ScenarioComparison(
        comparison_id=comparison_id,
        scenario_ids=tuple(scenario.scenario_id for scenario in scenarios),
        metrics=tuple(metrics),
        created_at=created_at or utc_now(),
    )
