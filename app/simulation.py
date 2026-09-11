"""Independent CRE simulation boundary.

This module models explicit uncertainty around CRE underwriting inputs and
feeds sampled values through the existing deterministic calculation engine.
Simulation outputs are modeled distributions, not evidence, recommendations,
or authorizations.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.scenario_analysis import CREScenarioAnalysis
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

DistributionType = Literal["uniform", "triangular"]
SimulationMetric = Literal[
    "effective_gross_income",
    "net_operating_income",
    "cap_rate",
    "implied_value",
    "loan_amount",
    "ltv",
    "annual_debt_service",
    "dscr",
    "cash_flow_after_debt_service",
    "cash_on_cash",
]

SimulationInputName = Literal[
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


class SimulationDistributionInput(BaseModel):
    """One explicit stochastic underwriting input."""

    model_config = ConfigDict(frozen=True)

    input_name: SimulationInputName
    deterministic_value: float
    lower_bound: float
    upper_bound: float
    distribution_type: DistributionType
    input_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_distribution(self) -> "SimulationDistributionInput":
        for name, value in (
            ("deterministic_value", self.deterministic_value),
            ("lower_bound", self.lower_bound),
            ("upper_bound", self.upper_bound),
        ):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound cannot exceed upper_bound")
        if not self.lower_bound <= self.deterministic_value <= self.upper_bound:
            raise ValueError("deterministic_value must be within bounds")
        if self.input_name == "ltv" and not 0 <= self.lower_bound <= self.upper_bound <= 1:
            raise ValueError("ltv bounds must be between 0 and 1")
        if self.input_name == "annual_interest_rate" and self.lower_bound < 0:
            raise ValueError("annual_interest_rate cannot be negative")
        if self.input_name == "principal" and self.lower_bound < 0:
            raise ValueError("principal cannot be negative")
        if self.input_name == "amortization_years" and self.lower_bound <= 0:
            raise ValueError("amortization_years bounds must be positive")
        return self


class SimulationThreshold(BaseModel):
    """An explicit descriptive threshold. It carries no judgment."""

    model_config = ConfigDict(frozen=True)

    operator: Literal["lt", "lte", "gt", "gte"]
    value: float
    label: str = Field(min_length=1)

    @model_validator(mode="after")
    def finite_threshold(self) -> "SimulationThreshold":
        if not isfinite(self.value):
            raise ValueError("threshold value must be finite")
        return self


class DistributionSummary(BaseModel):
    """Descriptive statistics for one modeled outcome distribution."""

    model_config = ConfigDict(frozen=True)

    metric: SimulationMetric
    iterations: int
    mean: float
    median: float
    minimum: float
    maximum: float
    percentiles: tuple[tuple[float, float], ...]
    threshold_probabilities: tuple[tuple[str, float], ...] = ()


class CRESimulation(BaseModel):
    """Immutable, reproducible CRE simulation artifact."""

    model_config = ConfigDict(frozen=True)

    simulation_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    scenario_ref: str = Field(min_length=1)
    metric: SimulationMetric
    inputs: tuple[SimulationDistributionInput, ...]
    thresholds: tuple[SimulationThreshold, ...] = ()
    iterations: int = Field(gt=0)
    seed: int
    distribution_configuration: tuple[tuple[str, str], ...]
    formula_version: str = "cre-underwriting-v1"
    summary: DistributionSummary
    provenance_refs: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    created_at: datetime
    status: Literal["simulated", "unresolved"] = "simulated"
    investment_authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    transaction_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False
    authorization_capability: Literal[False] = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sample(rng: random.Random, item: SimulationDistributionInput) -> float:
    if item.distribution_type == "uniform":
        return rng.uniform(item.lower_bound, item.upper_bound)
    return rng.triangular(item.lower_bound, item.upper_bound, item.deterministic_value)


def _calculate(metric: SimulationMetric, values: dict[str, float], refs: tuple[str, ...]) -> CalculationResult:
    """Dispatch to existing deterministic formulas; no financial formulas are duplicated."""
    if metric == "effective_gross_income":
        return effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
    if metric == "net_operating_income":
        egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
        return net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
    if metric == "cap_rate":
        egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
        noi = net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
        return cap_rate(noi.value, values["property_value"], input_refs=refs)
    if metric == "implied_value":
        egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
        noi = net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
        return implied_value(noi.value, values["cap_rate"], input_refs=refs)
    if metric == "loan_amount":
        return loan_amount(values["property_value"], values["ltv"], input_refs=refs)
    if metric == "ltv":
        return ltv(values["loan_amount"], values["property_value"], input_refs=refs)
    if metric == "annual_debt_service":
        return annual_debt_service(values["principal"], values["annual_interest_rate"], int(values["amortization_years"]), input_refs=refs)
    if metric == "dscr":
        debt = annual_debt_service(values["principal"], values["annual_interest_rate"], int(values["amortization_years"]), input_refs=refs)
        egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
        noi = net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
        return dscr(noi.value, debt.value, input_refs=refs)
    if metric == "cash_flow_after_debt_service":
        debt = annual_debt_service(values["principal"], values["annual_interest_rate"], int(values["amortization_years"]), input_refs=refs)
        egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
        noi = net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
        return cash_flow_after_debt_service(noi.value, debt.value, input_refs=refs)
    debt = annual_debt_service(values["principal"], values["annual_interest_rate"], int(values["amortization_years"]), input_refs=refs)
    egi = effective_gross_income(values["gross_potential_income"], values["vacancy_credit_loss"], input_refs=refs)
    noi = net_operating_income(egi.value, values["operating_expenses"], input_refs=refs)
    cash_flow = cash_flow_after_debt_service(noi.value, debt.value, input_refs=refs)
    return cash_on_cash(cash_flow.value, values["equity_invested"], input_refs=refs)


def _threshold_matches(value: float, threshold: SimulationThreshold) -> bool:
    return {
        "lt": value < threshold.value,
        "lte": value <= threshold.value,
        "gt": value > threshold.value,
        "gte": value >= threshold.value,
    }[threshold.operator]


def _percentile(sorted_values: list[float], percentile: float) -> float:
    position = (len(sorted_values) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def run_cre_simulation(
    *,
    simulation_id: str,
    scenario: CREScenarioAnalysis,
    metric: SimulationMetric,
    inputs: tuple[SimulationDistributionInput, ...],
    iterations: int,
    seed: int,
    thresholds: tuple[SimulationThreshold, ...] = (),
    uncertainty: tuple[str, ...] = (),
    created_at: datetime | None = None,
) -> CRESimulation:
    """Run a reproducible simulation from explicit distributions only."""
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    names = [item.input_name for item in inputs]
    if len(names) != len(set(names)):
        raise ValueError("Each simulation input may be specified at most once")

    base_values = scenario.inputs.model_dump()
    for item in inputs:
        base_values[item.input_name] = item.deterministic_value
    required = {
        "effective_gross_income": {"gross_potential_income", "vacancy_credit_loss"},
        "net_operating_income": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses"},
        "cap_rate": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses", "property_value"},
        "implied_value": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses", "cap_rate"},
        "loan_amount": {"property_value", "ltv"},
        "ltv": {"loan_amount", "property_value"},
        "annual_debt_service": {"principal", "annual_interest_rate", "amortization_years"},
        "dscr": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses", "principal", "annual_interest_rate", "amortization_years"},
        "cash_flow_after_debt_service": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses", "principal", "annual_interest_rate", "amortization_years"},
        "cash_on_cash": {"gross_potential_income", "vacancy_credit_loss", "operating_expenses", "principal", "annual_interest_rate", "amortization_years", "equity_invested"},
    }[metric]
    if any(base_values.get(name) is None for name in required):
        missing = tuple(sorted(name for name in required if base_values.get(name) is None))
        raise ValueError(f"Missing simulation inputs: {', '.join(missing)}")

    rng = random.Random(seed)
    outcomes: list[float] = []
    refs = (f"simulation:{simulation_id}", f"scenario:{scenario.scenario_id}")
    for _ in range(iterations):
        values = dict(base_values)
        for item in inputs:
            values[item.input_name] = _sample(rng, item)
        result = _calculate(metric, values, refs)
        if result.status != "calculated" or result.value is None or not isfinite(result.value):
            raise ValueError(f"Simulation produced unresolved/non-finite {metric}")
        outcomes.append(result.value)

    ordered = sorted(outcomes)
    percentile_values = tuple((p, _percentile(ordered, p)) for p in (5.0, 25.0, 50.0, 75.0, 95.0))
    threshold_probabilities = tuple(
        (threshold.label, sum(_threshold_matches(value, threshold) for value in outcomes) / iterations)
        for threshold in thresholds
    )
    summary = DistributionSummary(
        metric=metric,
        iterations=iterations,
        mean=sum(outcomes) / iterations,
        median=_percentile(ordered, 50.0),
        minimum=ordered[0],
        maximum=ordered[-1],
        percentiles=percentile_values,
        threshold_probabilities=threshold_probabilities,
    )
    return CRESimulation(
        simulation_id=simulation_id,
        scenario_id=scenario.scenario_id,
        scenario_ref=f"scenario:{scenario.scenario_id}",
        metric=metric,
        inputs=inputs,
        thresholds=thresholds,
        iterations=iterations,
        seed=seed,
        distribution_configuration=tuple((item.input_name, item.distribution_type) for item in inputs),
        formula_version="cre-underwriting-v1",
        summary=summary,
        provenance_refs=refs,
        uncertainty=uncertainty,
        created_at=created_at or utc_now(),
    )
