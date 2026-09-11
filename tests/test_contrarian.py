import pytest

from app.contrarian import ContrarianFinding, ContrarianValidationError, review_contrarian
from app.cre_simulation import CRESimulationConfig, run_cre_simulation
from app.proforma import ProFormaInput, calculate_proforma
from app.scenario import ScenarioDefinition, run_scenario, standard_scenarios


def base_input() -> ProFormaInput:
    return ProFormaInput(
        asset_id="asset-1",
        acquisition_price=10_000_000,
        acquisition_costs=250_000,
        projection_years=5,
        annual_rent=900_000,
        initial_occupancy=0.95,
        vacancy_rate=0,
        operating_expenses=250_000,
        entry_cap_rate=0.065,
        exit_cap_rate=0.06,
        rent_growth=0.04,
    )


def test_accepts_proforma_result_and_preserves_calculations():
    inputs = base_input()
    result = calculate_proforma(inputs)
    review = review_contrarian(case_identity="case-1", proforma=result)
    assert review.case_identity == "case-1"
    assert result.unlevered_irr is not None
    assert all(f.provenance != "RECOMMENDATION" for f in review.findings)


def test_reviews_scenario_and_simulation():
    inputs = base_input()
    scenario = run_scenario(inputs, standard_scenarios().scenarios[3])
    simulation = run_cre_simulation(
        inputs,
        standard_scenarios().scenarios[3],
        config=CRESimulationConfig(paths=100, horizon_steps=5, seed=7),
    )
    review = review_contrarian(
        case_identity="case-1",
        scenarios=[scenario],
        simulations=[simulation],
        evidence=[{"evidence_id": "e1", "claim": "lease rollover data", "source": "lease"}],
    )
    assert review.scenarios_reviewed == ["ADVERSARIAL"]
    assert review.simulations_reviewed == ["ADVERSARIAL:7"]
    simulation_findings = [f for f in review.findings if f.category == "MODEL"]
    assert simulation_findings[0].supporting_simulation_output["probability_loss"] == simulation.simulation["summary"]["probability_loss"]
    assert simulation_findings[0].provenance == "CALCULATION"


def test_scenario_comparison_is_non_destructive():
    inputs = base_input()
    definitions = standard_scenarios()
    results = [run_scenario(inputs, definition) for definition in definitions.scenarios]
    before = [result.model_dump() for result in results]
    review = review_contrarian(
        case_identity="case-1",
        scenarios=results,
        evidence=[{"evidence_id": "e1", "claim": "market rent", "source": "source"}],
    )
    assert set(review.scenarios_reviewed) == {"BASE", "UPSIDE", "DOWNSIDE", "ADVERSARIAL"}
    assert [result.model_dump() for result in results] == before


def test_missing_evidence_is_explicit():
    result = calculate_proforma(base_input())
    review = review_contrarian(case_identity="case-1", proforma=result)
    assert any(f.category == "EVIDENCE" and f.status == "INSUFFICIENT_DATA" for f in review.findings)
    assert review.margin_of_safety.status == "UNDETERMINED"


def test_agent_cannot_supply_authoritative_probability_or_irr():
    result = calculate_proforma(base_input())
    with pytest.raises(ContrarianValidationError):
        review_contrarian(
            case_identity="case-1",
            proforma=result,
            agent_perspectives=[{"agent_id": "contrarian-agent", "probability_loss": 0.12}],
        )
    with pytest.raises(ContrarianValidationError):
        review_contrarian(
            case_identity="case-1",
            proforma=result,
            agent_perspectives=[{"agent_id": "investor-agent", "irr": 0.18}],
        )


def test_simulation_outputs_are_not_recalculated():
    inputs = base_input()
    definition = ScenarioDefinition(name="BASE", description="Base")
    simulation = run_cre_simulation(inputs, definition, config=CRESimulationConfig(paths=100, horizon_steps=5, seed=42))
    review = review_contrarian(
        case_identity="case-1",
        scenarios=[run_scenario(inputs, definition)],
        simulations=[simulation],
        evidence=[{"evidence_id": "e1", "claim": "rent roll", "source": "source"}],
    )
    finding = next(f for f in review.findings if f.category == "MODEL")
    assert finding.supporting_simulation_output == simulation.simulation["summary"]


def test_contrarian_does_not_change_workflow_state():
    result = calculate_proforma(base_input())
    review = review_contrarian(
        case_identity="case-1",
        proforma=result,
        evidence=[{"evidence_id": "e1", "claim": "rent roll", "source": "source"}],
    )
    assert "workflow_state" not in review.model_dump()
    assert "authorization_id" not in review.model_dump()


def test_no_go_is_a_recommendation_type_not_authorization():
    finding = ContrarianFinding(
        category="ASSUMPTION",
        severity="CRITICAL",
        description="NO_GO_RECOMMENDATION",
        rationale="Insufficient margin of safety.",
        provenance="RECOMMENDATION",
        output_type="RECOMMENDATION",
    )
    assert finding.output_type == "RECOMMENDATION"
    assert finding.provenance == "RECOMMENDATION"
