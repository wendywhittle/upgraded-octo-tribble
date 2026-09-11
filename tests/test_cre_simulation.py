import copy

import pytest

from app.cre_simulation import (
    CRESimulationConfig,
    SimulationValidationError,
    run_cre_simulation,
    run_cre_simulation_from_proforma,
)
from app.proforma import ProFormaInput
from app.scenario import ScenarioDefinition


def base_input() -> ProFormaInput:
    return ProFormaInput(
        asset_id="SIM-001",
        acquisition_price=1_000_000,
        acquisition_costs=20_000,
        projection_years=3,
        annual_rent=100_000,
        initial_occupancy=0.95,
        vacancy_rate=0,
        rent_growth=0.04,
        operating_expenses=20_000,
        expense_growth=0.02,
        entry_cap_rate=0.08,
        exit_cap_rate=0.06,
        capex=5_000,
        reserves=2_000,
    )


def test_base_scenario_reaches_existing_monte_carlo_boundary():
    result = run_cre_simulation_from_proforma(
        base_input(), config=CRESimulationConfig(paths=100, seed=7)
    )
    assert result.simulation["engine"].startswith("AletheiaTelos Independent Monte Carlo")
    assert result.simulation["independent_of_agents"] is True
    assert result.simulation_regime == "base"


def test_downside_and_adversarial_preserve_scenario_identity():
    base = base_input()
    downside = ScenarioDefinition(
        name="DOWNSIDE",
        description="Downside hypothesis",
        overrides={"rent_growth": 0.01, "initial_occupancy": 0.88, "exit_cap_rate": 0.0675},
        provenance={"assumption_type": "HYPOTHESIS"},
    )
    adversarial = ScenarioDefinition(
        name="ADVERSARIAL",
        description="Adverse hypothesis",
        overrides={
            "rent_growth": 0.0,
            "initial_occupancy": 0.82,
            "exit_cap_rate": 0.075,
            "expense_growth": 0.05,
        },
        provenance={"assumption_type": "HYPOTHESIS"},
    )
    d = run_cre_simulation(base, downside, config=CRESimulationConfig(paths=100, seed=11))
    a = run_cre_simulation(base, adversarial, config=CRESimulationConfig(paths=100, seed=11))
    assert d.scenario.name == "DOWNSIDE"
    assert d.scenario.overrides["initial_occupancy"] == 0.88
    assert d.simulation_regime == "bear"
    assert a.scenario.name == "ADVERSARIAL"
    assert a.simulation_regime == "adversarial"


def test_custom_scenario_requires_explicit_regime():
    scenario = ScenarioDefinition(
        name="CUSTOM",
        description="Custom hypothesis",
        overrides={"rent_growth": 0.03},
    )
    with pytest.raises(SimulationValidationError, match="explicit simulation regime"):
        run_cre_simulation(base_input(), scenario, config=CRESimulationConfig(paths=100))


def test_custom_scenario_with_regime_works():
    scenario = ScenarioDefinition(
        name="CUSTOM",
        description="Custom hypothesis",
        overrides={"rent_growth": 0.03},
    )
    result = run_cre_simulation(
        base_input(), scenario,
        config=CRESimulationConfig(paths=100, seed=3, regime="base"),
    )
    assert result.scenario.name == "CUSTOM"
    assert result.simulation_regime == "base"


def test_invalid_simulation_configuration_is_rejected_by_pydantic():
    with pytest.raises(ValueError):
        CRESimulationConfig(paths=0)
    with pytest.raises(ValueError):
        CRESimulationConfig(horizon_steps=0)


def test_invalid_scenario_assumptions_fail():
    scenario = ScenarioDefinition(
        name="BAD",
        description="Invalid",
        overrides={"initial_occupancy": 1.1},
    )
    with pytest.raises(SimulationValidationError):
        run_cre_simulation(base_input(), scenario, config=CRESimulationConfig(paths=100))


def test_calculated_outputs_cannot_be_simulation_assumptions():
    scenario = ScenarioDefinition(
        name="BAD",
        description="Agent output masquerading as an input",
        overrides={"unlevered_irr": 0.18},
    )
    with pytest.raises(SimulationValidationError):
        run_cre_simulation(base_input(), scenario, config=CRESimulationConfig(paths=100))


def test_same_input_and_seed_are_reproducible():
    config = CRESimulationConfig(paths=100, seed=42)
    first = run_cre_simulation_from_proforma(base_input(), config=config).model_dump(mode="json")
    second = run_cre_simulation_from_proforma(base_input(), config=config).model_dump(mode="json")
    assert first == second


def test_different_seed_can_change_simulation_output():
    first = run_cre_simulation_from_proforma(
        base_input(), config=CRESimulationConfig(paths=100, seed=42)
    )
    second = run_cre_simulation_from_proforma(
        base_input(), config=CRESimulationConfig(paths=100, seed=43)
    )
    assert first.simulation["summary"] != second.simulation["summary"]


def test_adapter_does_not_mutate_proforma_or_scenario():
    base = base_input()
    scenario = ScenarioDefinition(
        name="DOWNSIDE",
        description="Downside",
        overrides={"initial_occupancy": 0.88},
    )
    base_before = copy.deepcopy(base.model_dump(mode="python"))
    scenario_before = copy.deepcopy(scenario.model_dump(mode="python"))
    run_cre_simulation(base, scenario, config=CRESimulationConfig(paths=100, seed=5))
    assert base.model_dump(mode="python") == base_before
    assert scenario.model_dump(mode="python") == scenario_before


def test_simulation_outputs_are_calculations_and_proforma_remains_authoritative():
    result = run_cre_simulation_from_proforma(
        base_input(), config=CRESimulationConfig(paths=100, seed=9)
    )
    assert result.output_types["probability_loss"] == "CALCULATION"
    assert result.proforma.output_types["unlevered_irr"] == "CALCULATION"
    assert "probability_loss" in result.simulation["summary"]
