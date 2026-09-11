"""CRE-to-Monte-Carlo simulation adapter.

This module translates deterministic CRE underwriting/scenario results into the
existing independent Monte Carlo engine. It does not perform stochastic
calculations itself and does not alter workflow or authorization state.
"""
from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.proforma import ProFormaInput, ProFormaResult, calculate_proforma
from app.scenario import ScenarioDefinition, ScenarioResult, run_scenario
from app.simulator import run_monte_carlo


class SimulationValidationError(ValueError):
    """Raised when CRE simulation configuration is invalid."""


class CRESimulationConfig(BaseModel):
    """Explicit, reproducible configuration for the existing Monte Carlo engine."""

    model_config = ConfigDict(extra="forbid")

    paths: int = Field(default=5000, ge=100, le=100_000)
    horizon_steps: int | None = Field(default=None, ge=1, le=1000)
    seed: int = 42
    regime: Literal["base", "bull", "bear", "adversarial"] | None = None


class CRESimulationResult(BaseModel):
    """Machine-readable result preserving CRE and simulation provenance."""

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioDefinition
    base_input_version: str = "1"
    simulation_config: CRESimulationConfig
    simulation_regime: str
    proforma: ProFormaResult
    simulation: Dict[str, Any]
    output_types: Dict[str, str] = Field(default_factory=lambda: {
        "simulation": "CALCULATION",
        "mean_terminal": "CALCULATION",
        "median_terminal": "CALCULATION",
        "p05_terminal": "CALCULATION",
        "p95_terminal": "CALCULATION",
        "probability_loss": "CALCULATION",
        "max_drawdown_mean": "CALCULATION",
    })


_SCENARIO_TO_REGIME = {
    "BASE": "base",
    "UPSIDE": "bull",
    "DOWNSIDE": "bear",
    "ADVERSARIAL": "adversarial",
}


def _validate_scenario_input(base_input: ProFormaInput, scenario: ScenarioDefinition) -> None:
    """Force scenario overrides through the existing Scenario Engine validation."""
    try:
        run_scenario(base_input, scenario)
    except ValueError as exc:
        raise SimulationValidationError(str(exc)) from exc


def run_cre_simulation(
    base_input: ProFormaInput,
    scenario: ScenarioDefinition,
    *,
    config: CRESimulationConfig | None = None,
    base_input_version: str = "1",
) -> CRESimulationResult:
    """Run a CRE scenario through the existing independent Monte Carlo engine.

    Phase 4 deliberately maps the deterministic CRE scenario to one of the
    existing simulator's explicit regimes. The simulator remains authoritative
    for stochastic outputs. CRE-specific stochastic modeling of individual
    rent, occupancy, expense, and cap-rate distributions is a future extension
    of the simulator contract, not duplicated here.
    """
    config = config or CRESimulationConfig()
    _validate_scenario_input(base_input, scenario)

    scenario_result: ScenarioResult = run_scenario(
        base_input, scenario, base_input_version=base_input_version
    )
    regime = config.regime or _SCENARIO_TO_REGIME.get(scenario.name.upper())
    if regime is None:
        raise SimulationValidationError(
            "Custom scenarios require an explicit simulation regime"
        )

    horizon_steps = config.horizon_steps or scenario_result.proforma.annual.__len__()
    assumptions = [
        f"CRE scenario: {scenario.name}",
        f"Simulation regime: {regime}",
        "CRE scenario overrides are hypotheses, not simulation outputs.",
        "Simulation outputs are calculated by the independent Monte Carlo engine.",
    ]

    # The current simulator exposes a generic asset-value path interface. The
    # acquisition basis is the capital-at-risk baseline; no CRE formulas are
    # reproduced here. Existing regime parameters remain inside simulator.py.
    simulation = run_monte_carlo(
        initial_value=scenario_result.proforma.acquisition_basis,
        horizon_steps=horizon_steps,
        paths=config.paths,
        seed=config.seed,
        assumptions=assumptions,
    )

    selected = next(
        summary for summary in simulation["scenarios"] if summary["scenario"] == regime
    )

    return CRESimulationResult(
        scenario=scenario,
        base_input_version=base_input_version,
        simulation_config=config.model_copy(update={"horizon_steps": horizon_steps}),
        simulation_regime=regime,
        proforma=scenario_result.proforma,
        simulation={
            "engine": simulation["engine"],
            "independent_of_agents": simulation["independent_of_agents"],
            "paths": simulation["paths"],
            "horizon_steps": simulation["horizon_steps"],
            "seed": simulation["seed"],
            "summary": selected,
            "assumptions": simulation["assumptions"],
        },
    )


def run_cre_simulation_from_proforma(
    proforma_input: ProFormaInput,
    *,
    config: CRESimulationConfig | None = None,
    base_input_version: str = "1",
) -> CRESimulationResult:
    """Convenience entry point for the base underwriting case."""
    scenario = ScenarioDefinition(
        name="BASE",
        description="Base underwriting case with no scenario overrides.",
        provenance={"assumption_type": "HYPOTHESIS"},
    )
    return run_cre_simulation(
        proforma_input,
        scenario,
        config=config,
        base_input_version=base_input_version,
    )
