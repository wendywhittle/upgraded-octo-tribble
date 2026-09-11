from datetime import datetime, timezone

import pytest

from app.scenario_analysis import ScenarioOverride, build_cre_scenario
from app.simulation import (
    CRESimulation,
    SimulationDistributionInput,
    SimulationThreshold,
    run_cre_simulation,
)
from app.underwriting import (
    AcquisitionTerms,
    OperatingAssumptions,
    PropertyIdentity,
    UnderwritingProvenance,
    ValuationAssumptions,
    build_cre_underwriting,
)


FIXED = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_scenario():
    provenance = UnderwritingProvenance(status="assumed")
    underwriting = build_cre_underwriting(
        underwriting_id="uw-sim-1",
        property=PropertyIdentity(property_id="property-sim-1"),
        acquisition=AcquisitionTerms(purchase_price=10_000_000, provenance=provenance),
        operations=OperatingAssumptions(gross_revenue=1_000_000, operating_expenses=300_000, provenance=provenance),
        valuation=ValuationAssumptions(exit_cap_rate=0.065, provenance=provenance),
        created_at=FIXED,
    )
    return build_cre_scenario(
        scenario_id="scenario-sim-1",
        scenario_name="Simulation Base",
        scenario_type="base",
        underwriting=underwriting,
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=50_000),),
        created_at=FIXED,
    )


def make_inputs():
    return (
        SimulationDistributionInput(
            input_name="operating_expenses",
            deterministic_value=300_000,
            lower_bound=280_000,
            upper_bound=320_000,
            distribution_type="uniform",
            input_ref="assumption:opex-range",
        ),
    )


def test_simulation_is_constructed_and_immutable():
    simulation = run_cre_simulation(
        simulation_id="sim-1",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=100,
        seed=7,
        created_at=FIXED,
    )
    assert isinstance(simulation, CRESimulation)
    assert simulation.investment_authority == "none"
    assert simulation.execution_capability is False
    assert simulation.portfolio_mutation is False
    with pytest.raises((TypeError, ValueError)):
        simulation.seed = 8


def test_same_seed_and_configuration_are_reproducible():
    kwargs = dict(
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=500,
        seed=42,
        created_at=FIXED,
    )
    first = run_cre_simulation(simulation_id="sim-repro", **kwargs)
    second = run_cre_simulation(simulation_id="sim-repro", **kwargs)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_different_seed_changes_stochastic_samples():
    kwargs = dict(
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=100,
        created_at=FIXED,
    )
    first = run_cre_simulation(simulation_id="sim-a", seed=1, **kwargs)
    second = run_cre_simulation(simulation_id="sim-b", seed=2, **kwargs)
    assert first.summary.mean != second.summary.mean


def test_distribution_and_bounds_are_explicit():
    item = make_inputs()[0]
    assert item.distribution_type == "uniform"
    assert item.lower_bound == 280_000
    assert item.upper_bound == 320_000
    assert item.deterministic_value == 300_000
    assert item.input_ref == "assumption:opex-range"


def test_threshold_probability_is_descriptive_only():
    simulation = run_cre_simulation(
        simulation_id="sim-threshold",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=200,
        seed=9,
        thresholds=(SimulationThreshold(operator="lt", value=390_000, label="below-390k"),),
        created_at=FIXED,
    )
    probability = dict(simulation.summary.threshold_probabilities)["below-390k"]
    assert 0 <= probability <= 1
    dumped = simulation.model_dump()
    assert "recommendation" not in dumped


def test_missing_inputs_are_not_silently_zeroed():
    with pytest.raises(ValueError, match="Missing simulation inputs"):
        run_cre_simulation(
            simulation_id="sim-missing",
            scenario=make_scenario(),
            metric="cash_on_cash",
            inputs=(),
            iterations=10,
            seed=1,
            created_at=FIXED,
        )


def test_invalid_bounds_and_iterations_are_rejected():
    with pytest.raises(ValueError):
        SimulationDistributionInput(
            input_name="operating_expenses",
            deterministic_value=300,
            lower_bound=400,
            upper_bound=200,
            distribution_type="uniform",
            input_ref="assumption:test",
        )
    with pytest.raises(ValueError):
        run_cre_simulation(
            simulation_id="sim-invalid",
            scenario=make_scenario(),
            metric="net_operating_income",
            inputs=make_inputs(),
            iterations=0,
            seed=1,
            created_at=FIXED,
        )


def test_non_finite_and_invalid_metric_inputs_are_rejected():
    with pytest.raises(ValueError):
        SimulationDistributionInput(
            input_name="operating_expenses",
            deterministic_value=float("inf"),
            lower_bound=1,
            upper_bound=2,
            distribution_type="uniform",
            input_ref="assumption:test",
        )


def test_simulation_reuses_existing_calculation_formula_version():
    simulation = run_cre_simulation(
        simulation_id="sim-formula",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=10,
        seed=3,
        created_at=FIXED,
    )
    assert simulation.formula_version == "cre-underwriting-v1"


def test_simulation_has_provenance_and_serializes():
    simulation = run_cre_simulation(
        simulation_id="sim-provenance",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=10,
        seed=3,
        created_at=FIXED,
    )
    assert simulation.scenario_ref == "scenario:scenario-sim-1"
    assert simulation.provenance_refs == ("simulation:sim-provenance", "scenario:scenario-sim-1")
    assert simulation.model_dump(mode="json")["status"] == "simulated"


def test_simulation_has_no_authority_or_recommendation_logic():
    simulation = run_cre_simulation(
        simulation_id="sim-governance",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=make_inputs(),
        iterations=10,
        seed=3,
        created_at=FIXED,
    )
    dumped = simulation.model_dump()
    assert dumped["investment_authority"] == "none"
    assert dumped["execution_capability"] is False
    assert dumped["transaction_capability"] is False
    assert dumped["portfolio_mutation"] is False
    assert dumped["authorization_capability"] is False
    assert not any(key in dumped for key in ("recommendation", "decision", "authorization"))


def test_triangular_distribution_uses_explicit_deterministic_mode():
    item = SimulationDistributionInput(
        input_name="operating_expenses",
        deterministic_value=300_000,
        lower_bound=200_000,
        upper_bound=400_000,
        distribution_type="triangular",
        input_ref="assumption:opex-triangular",
    )
    simulation = run_cre_simulation(
        simulation_id="sim-triangular",
        scenario=make_scenario(),
        metric="net_operating_income",
        inputs=(item,),
        iterations=100,
        seed=5,
        created_at=FIXED,
    )
    assert simulation.summary.minimum >= 350_000
    assert simulation.summary.maximum <= 550_000
