import pytest

from app.contrarian import review_contrarian
from app.cre_simulation import CRESimulationConfig, run_cre_simulation
from app.investment_synthesis import (
    SynthesisValidationError,
    apply_synthesis_to_case,
    synthesize_investment_case,
)
from app.proforma import ProFormaInput, calculate_proforma
from app.scenario import run_scenario, standard_scenarios
from app.workflow import InvestmentCase, WorkflowState


def base_input():
    return ProFormaInput(
        asset_id="asset-1", acquisition_price=10_000_000, acquisition_costs=250_000,
        projection_years=5, annual_rent=900_000, initial_occupancy=0.95,
        vacancy_rate=0, operating_expenses=250_000, entry_cap_rate=0.065,
        exit_cap_rate=0.06, rent_growth=0.04,
    )


def test_synthesizes_proforma_scenarios_simulations_and_contrarian():
    inputs = base_input(); definitions = standard_scenarios()
    proforma = calculate_proforma(inputs)
    scenarios = [run_scenario(inputs, d) for d in definitions.scenarios]
    simulations = [run_cre_simulation(inputs, d, config=CRESimulationConfig(paths=100, horizon_steps=5, seed=42)) for d in definitions.scenarios]
    contrarian = review_contrarian(case_identity="case-1", proforma=proforma, scenarios=scenarios, simulations=simulations, evidence=[{"evidence_id": "e1", "claim": "rent roll", "source": "lease"}])
    result = synthesize_investment_case(case_identity="case-1", proforma=proforma, scenarios=scenarios, simulations=simulations, contrarian=contrarian, evidence=[{"evidence_id": "e1", "claim": "rent roll", "source": "lease"}], agent_perspectives=[{"agent_id": "investor", "assumptions": ["Stable tenancy"]}])
    assert result.contrarian_reviewed is True
    assert set(result.scenarios_reviewed) == {"BASE", "UPSIDE", "DOWNSIDE", "ADVERSARIAL"}
    assert result.thesis_status in {"CONDITIONAL", "FRAGILE", "SUPPORTED"}
    assert result.output_type == "INTERPRETATION"


def test_scenario_and_simulation_interpretation_consumes_existing_outputs():
    inputs = base_input(); defs = standard_scenarios()
    scenarios = [run_scenario(inputs, d) for d in defs.scenarios]
    simulations = [run_cre_simulation(inputs, d, config=CRESimulationConfig(paths=100, horizon_steps=5, seed=7)) for d in defs.scenarios]
    before = [x.model_dump() for x in scenarios] + [x.model_dump() for x in simulations]
    result = synthesize_investment_case(case_identity="case-1", scenarios=scenarios, simulations=simulations)
    assert any("probability_loss" in x for x in result.synthesis + " ".join(result.thesis.scenario_resilience))
    assert [x.model_dump() for x in scenarios] + [x.model_dump() for x in simulations] == before


def test_disagreement_is_preserved():
    result = synthesize_investment_case(
        case_identity="case-1",
        evidence=[{"evidence_id": "e1", "claim": "market rent", "source": "A"}],
        disagreements=[{"topic": "Market rent", "status": "MATERIAL_DISAGREEMENT", "perspectives": ["researcher", "investor"], "positions": ["stable", "declining"], "unresolved_questions": ["Which rent estimate is supported?"]}],
    )
    assert result.disagreements[0].status == "MATERIAL_DISAGREEMENT"
    assert "Which rent estimate is supported?" in result.unresolved_questions
    assert result.thesis_status == "CONDITIONAL"


def test_contradictory_evidence_is_not_silently_resolved():
    result = synthesize_investment_case(
        case_identity="case-1",
        evidence=[
            {"evidence_id": "e1", "claim": "tenant retention", "source": "lease", "contradictory": True},
            {"evidence_id": "e2", "claim": "tenant retention", "source": "broker", "contradictory": True},
        ],
    )
    assert any("Contradictory evidence" in q for q in result.unresolved_questions)


def test_missing_data_is_explicit():
    result = synthesize_investment_case(case_identity="case-1", evidence=[])
    assert result.thesis_status == "UNDETERMINED"
    assert result.thesis.unresolved_questions == []


def test_invalid_input_fails_explicitly():
    with pytest.raises(SynthesisValidationError):
        synthesize_investment_case(case_identity="   ")
    with pytest.raises(SynthesisValidationError):
        synthesize_investment_case(case_identity="case-1", evidence=[{"evidence_id": "e1"}], disagreements=[{"status": "MAGICAL"}])


def test_agent_probability_and_irr_cannot_become_authoritative():
    for key, value in [("probability_loss", 0.12), ("irr", 0.18), ("unlevered_irr", 0.18)]:
        with pytest.raises(SynthesisValidationError):
            synthesize_investment_case(case_identity="case-1", evidence=[{"evidence_id": "e1", "claim": "x"}], agent_perspectives=[{"agent_id": "quant", key: value}])


def test_no_numerical_investment_score_is_created():
    result = synthesize_investment_case(case_identity="case-1", evidence=[{"evidence_id": "e1", "claim": "x"}])
    assert "score" not in result.model_dump()
    assert result.output_type == "INTERPRETATION"


def test_investment_case_integration_is_copy_only():
    case = InvestmentCase(deal_id="case-1", workflow_state=WorkflowState.AWAITING_INVESTMENT_APPROVAL, human_authorizations=["auth-1"])
    result = synthesize_investment_case(case_identity="case-1", evidence=[{"evidence_id": "e1", "claim": "x"}])
    updated = apply_synthesis_to_case(case, result)
    assert updated is not case
    assert case.investment_thesis is None
    assert updated.investment_thesis is not None
    assert updated.workflow_state == WorkflowState.AWAITING_INVESTMENT_APPROVAL
    assert updated.human_authorizations == ["auth-1"]


def test_case_identity_mismatch_cannot_integrate():
    case = InvestmentCase(deal_id="deal-1")
    result = synthesize_investment_case(case_identity="case-1", evidence=[{"evidence_id": "e1", "claim": "x"}])
    with pytest.raises(SynthesisValidationError):
        apply_synthesis_to_case(case, result)


def test_no_go_recommendation_remains_recommendation_only():
    from app.contrarian import ContrarianFinding
    finding = ContrarianFinding(category="ASSUMPTION", severity="CRITICAL", description="NO_GO_RECOMMENDATION", rationale="Insufficient support", provenance="RECOMMENDATION", output_type="RECOMMENDATION")
    assert finding.output_type == "RECOMMENDATION"
    assert finding.provenance == "RECOMMENDATION"
