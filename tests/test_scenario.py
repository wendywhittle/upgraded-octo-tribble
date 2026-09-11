import pytest

from app.proforma import ProFormaInput, calculate_proforma
from app.scenario import (
    ScenarioDefinition,
    ScenarioSet,
    ScenarioValidationError,
    run_scenario,
    run_scenario_set,
    standard_scenarios,
)


def base_input() -> ProFormaInput:
    return ProFormaInput(
        asset_id="SCENARIO-001",
        acquisition_price=1_000_000,
        acquisition_costs=20_000,
        projection_years=3,
        annual_rent=100_000,
        other_income=0,
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


def test_base_scenario_reproduces_base_proforma():
    base = base_input()
    result = run_scenario(base, ScenarioDefinition(name="BASE", description="Base"))
    assert result.proforma == calculate_proforma(base)


def test_downside_changes_only_explicit_overrides():
    base = base_input()
    base_result = calculate_proforma(base)
    scenario = ScenarioDefinition(
        name="DOWNSIDE",
        description="Downside",
        overrides={"rent_growth": 0.01, "initial_occupancy": 0.88, "exit_cap_rate": 0.0675},
    )
    result = run_scenario(base, scenario)
    assert result.proforma.annual[0].effective_gross_income < base_result.annual[0].effective_gross_income
    assert result.proforma.exit_valuation != base_result.exit_valuation
    assert base.rent_growth == 0.04
    assert base.initial_occupancy == 0.95
    assert base.exit_cap_rate == 0.06


def test_standard_scenarios_include_required_cases():
    names = [s.name for s in standard_scenarios().scenarios]
    assert names == ["BASE", "UPSIDE", "DOWNSIDE", "ADVERSARIAL"]


def test_custom_scenario_works():
    result = run_scenario(base_input(), ScenarioDefinition(
        name="CUSTOM", description="Custom", overrides={"expense_growth": 0.03}
    ))
    assert result.scenario.name == "CUSTOM"
    assert result.scenario.overrides["expense_growth"] == 0.03


def test_scenario_set_runs_independently_and_deterministically():
    base = base_input()
    scenarios = ScenarioSet(scenarios=[
        ScenarioDefinition(name="BASE", description="Base"),
        ScenarioDefinition(name="DOWN", description="Down", overrides={"initial_occupancy": 0.88}),
    ])
    first = run_scenario_set(base, scenarios).model_dump(mode="json")
    second = run_scenario_set(base, scenarios).model_dump(mode="json")
    assert first == second
    assert base.initial_occupancy == 0.95


@pytest.mark.parametrize("overrides", [
    {"unknown_field": 1},
    {"initial_occupancy": 1.1},
    {"exit_cap_rate": 0},
    {"rent_growth": -1.1},
    {"operating_expenses": -1},
    {"unlevered_irr": 0.07},
])
def test_invalid_or_calculated_output_overrides_fail(overrides):
    with pytest.raises(ScenarioValidationError):
        run_scenario(base_input(), ScenarioDefinition(name="INVALID", description="Invalid", overrides=overrides))


def test_scenario_identity_and_provenance_are_retained():
    scenario = ScenarioDefinition(
        name="DOWNSIDE",
        description="Hypothesis",
        overrides={"initial_occupancy": 0.88},
        provenance={"assumption_type": "HYPOTHESIS", "source": "scenario-design"},
    )
    result = run_scenario(base_input(), scenario, base_input_version="7")
    assert result.base_input_version == "7"
    assert result.scenario.provenance["assumption_type"] == "HYPOTHESIS"
    assert result.scenario.overrides["initial_occupancy"] == 0.88


def test_agent_style_financial_output_cannot_become_scenario_result():
    scenario = ScenarioDefinition(name="AGENT-PROPOSED", description="Agent proposal", overrides={"rent_growth": 0.04})
    result = run_scenario(base_input(), scenario)
    assert result.proforma.output_types["unlevered_irr"] == "CALCULATION"
    assert result.proforma.unlevered_irr != 0.18
