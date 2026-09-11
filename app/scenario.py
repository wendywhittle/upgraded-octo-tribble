"""Deterministic CRE scenario layer.

Scenarios vary validated underwriting assumptions. The Pro Forma Engine remains
responsible for every financial calculation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.proforma import ProFormaInput, ProFormaResult, calculate_proforma


class ScenarioValidationError(ValueError):
    """Raised when a scenario contains invalid or non-input overrides."""


class ScenarioDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    overrides: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "description")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("scenario name and description are required")
        return value


class ScenarioSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenarios: List[ScenarioDefinition] = Field(min_length=1)


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioDefinition
    base_input_version: str = "1"
    proforma: ProFormaResult


class ScenarioSetResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: List[ScenarioResult]


def _input_field_names() -> set[str]:
    return set(ProFormaInput.model_fields)


def _build_input(base: ProFormaInput, overrides: Dict[str, Any]) -> ProFormaInput:
    allowed = _input_field_names()
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ScenarioValidationError(
            f"Unknown scenario override(s): {', '.join(unknown)}"
        )
    values = base.model_dump(mode="python")
    values.update(overrides)
    try:
        return ProFormaInput.model_validate(values)
    except ValueError as exc:
        raise ScenarioValidationError(str(exc)) from exc


def run_scenario(
    base_input: ProFormaInput,
    scenario: ScenarioDefinition,
    *,
    base_input_version: str = "1",
) -> ScenarioResult:
    """Run one scenario through the deterministic Pro Forma Engine."""
    scenario_input = _build_input(base_input, scenario.overrides)
    result = calculate_proforma(scenario_input)
    return ScenarioResult(
        scenario=scenario,
        base_input_version=base_input_version,
        proforma=result,
    )


def run_scenario_set(
    base_input: ProFormaInput,
    scenario_set: ScenarioSet,
    *,
    base_input_version: str = "1",
) -> ScenarioSetResult:
    """Run each scenario independently against the same base underwriting."""
    return ScenarioSetResult(
        results=[
            run_scenario(base_input, scenario, base_input_version=base_input_version)
            for scenario in scenario_set.scenarios
        ]
    )


def standard_scenarios() -> ScenarioSet:
    """Return explicit scenario hypotheses; BASE intentionally has no overrides."""
    return ScenarioSet(
        scenarios=[
            ScenarioDefinition(
                name="BASE",
                description="Base underwriting case with no scenario overrides.",
                provenance={"assumption_type": "HYPOTHESIS"},
            ),
            ScenarioDefinition(
                name="UPSIDE",
                description="Illustrative upside hypothesis; values must be reviewed for the deal.",
                overrides={
                    "rent_growth": 0.05,
                    "initial_occupancy": 0.97,
                    "exit_cap_rate": 0.0575,
                },
                provenance={"assumption_type": "HYPOTHESIS"},
            ),
            ScenarioDefinition(
                name="DOWNSIDE",
                description="Illustrative downside hypothesis; values must be reviewed for the deal.",
                overrides={
                    "rent_growth": 0.01,
                    "initial_occupancy": 0.88,
                    "exit_cap_rate": 0.0675,
                },
                provenance={"assumption_type": "HYPOTHESIS"},
            ),
            ScenarioDefinition(
                name="ADVERSARIAL",
                description="Illustrative adverse hypothesis designed to expose material downside.",
                overrides={
                    "rent_growth": 0.0,
                    "initial_occupancy": 0.82,
                    "exit_cap_rate": 0.075,
                    "expense_growth": 0.05,
                },
                provenance={"assumption_type": "HYPOTHESIS"},
            ),
        ]
    )
