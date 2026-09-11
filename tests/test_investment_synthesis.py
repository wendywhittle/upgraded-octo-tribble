import copy

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
from app.workflow import InvestmentCase, Opportunity, WorkflowService, WorkflowState


def base_input():
    return ProFormaInput(
        asset_id="asset-1", acquisition_price=10_000_000, acquisition_costs=250_000,
        projection_years=5, annual_rent=900_000, initial_occupancy=0.95,
        vacancy_rate=0, operating_expenses=250_000, entry_cap_rate=0.065,
        exit_cap_rate=0.06, rent_growth=0.04,
    )


def analytical_fixture(seed=42):
    inputs = base_input()
    definitions = standard_scenarios()
    proforma = calculate_proforma(inputs)
    scenarios = [run_scenario(inputs, d) for d in definitions.scenarios]
    simulations = [
        run_cre_simulation(
            inputs, d,
            config=CRESimulationConfig(paths=100, horizon_steps=5, seed=seed),
        )
        for d in definitions.scenarios
    ]
    evidence = [{"evidence_id": "e1", "claim": "rent roll supports current rent", "source": "lease"}]
    contrarian = review_contrarian(
        case_identity="case-1",
        proforma=proforma,
        scenarios=scenarios,
        simulations=simulations,
        evidence=evidence,
    )
    return inputs, proforma, scenarios, simulations, evidence, contrarian


def test_synthesizes_complete_investment_case():
    _, proforma, scenarios, simulations, evidence, contrarian = analytical_fixture()
    result = synthesize_investment_case(
        case_identity="case-1", proforma=proforma, scenarios=scenarios,
        simulations=simulations, contrarian=contrarian, evidence=evidence,
        agent_perspectives=[{"agent_id": "investor", "assumptions": ["Stable tenancy"]}],
    )
    assert result.contrarian_reviewed is True
    assert set(result.scenarios_reviewed) == {"BASE", "UPSIDE", "DOWNSIDE", "ADVERSARIAL"}
    assert result.thesis_status in {"CONDITIONAL", "FRAGILE", "SUPPORTED"}
    assert result.output_type == "INTERPRETATION"
    assert result.provenance["layers"][-1] == "CONTRARIAN"


def test_scenario_and_simulation_interpretation_consumes_existing_outputs():
    _, _, scenarios, simulations, _, _ = analytical_fixture(seed=7)
    before = [copy.deepcopy(x.model_dump()) for x in scenarios] + [copy.deepcopy(x.model_dump()) for x in simulations]
    result = synthesize_investment_case(case_identity="case-1", scenarios=scenarios, simulations=simulations)
    combined = " ".join(result.thesis.scenario_resilience)
    assert "probability_loss" in combined
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
        case_identity="case-1", proforma=calculate_proforma(base_input()),
        evidence=[
            {"evidence_id": "e1", "claim": "tenant retention", "source": "lease", "contradictory": True},
            {"evidence_id": "e2", "claim": "tenant retention", "source": "broker", "contradictory": True},
        ],
    )
    assert any("Contradictory evidence" in q for q in result.unresolved_questions)


def test_missing_data_fails_explicitly_instead_of_fabricating_synthesis():
    with pytest.raises(SynthesisValidationError):
        synthesize_investment_case(case_identity="case-1", evidence=[])


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
    result = synthesize_investment_case(case_identity="case-1", proforma=calculate_proforma(base_input()))
    assert "score" not in result.model_dump()
    assert result.output_type == "INTERPRETATION"


def test_investment_case_integration_is_copy_only():
    case = InvestmentCase(deal_id="case-1", workflow_state=WorkflowState.AWAITING_INVESTMENT_APPROVAL, human_authorizations=["auth-1"])
    result = synthesize_investment_case(case_identity="case-1", proforma=calculate_proforma(base_input()))
    updated = apply_synthesis_to_case(case, result)
    assert updated is not case
    assert case.investment_thesis is None
    assert updated.investment_thesis is not None
    assert updated.workflow_state == WorkflowState.AWAITING_INVESTMENT_APPROVAL
    assert updated.human_authorizations == ["auth-1"]


def test_case_identity_mismatch_cannot_integrate():
    case = InvestmentCase(deal_id="deal-1")
    result = synthesize_investment_case(case_identity="case-1", proforma=calculate_proforma(base_input()))
    with pytest.raises(SynthesisValidationError):
        apply_synthesis_to_case(case, result)


def test_no_go_recommendation_remains_recommendation_only():
    from app.contrarian import ContrarianFinding
    finding = ContrarianFinding(category="ASSUMPTION", severity="CRITICAL", description="NO_GO_RECOMMENDATION", rationale="Insufficient support", provenance="RECOMMENDATION", output_type="RECOMMENDATION")
    assert finding.output_type == "RECOMMENDATION"
    assert finding.provenance == "RECOMMENDATION"


def test_upstream_results_are_not_mutated_by_synthesis():
    _, proforma, scenarios, simulations, evidence, contrarian = analytical_fixture()
    snapshots = {
        "proforma": copy.deepcopy(proforma.model_dump()),
        "scenarios": copy.deepcopy([x.model_dump() for x in scenarios]),
        "simulations": copy.deepcopy([x.model_dump() for x in simulations]),
        "contrarian": copy.deepcopy(contrarian.model_dump()),
    }
    synthesize_investment_case(case_identity="case-1", proforma=proforma, scenarios=scenarios, simulations=simulations, contrarian=contrarian, evidence=evidence)
    assert proforma.model_dump() == snapshots["proforma"]
    assert [x.model_dump() for x in scenarios] == snapshots["scenarios"]
    assert [x.model_dump() for x in simulations] == snapshots["simulations"]
    assert contrarian.model_dump() == snapshots["contrarian"]


def test_identical_inputs_produce_identical_synthesis():
    _, proforma, scenarios, simulations, evidence, contrarian = analytical_fixture(seed=19)
    first = synthesize_investment_case(case_identity="case-1", proforma=proforma, scenarios=scenarios, simulations=simulations, contrarian=contrarian, evidence=evidence)
    second = synthesize_investment_case(case_identity="case-1", proforma=proforma, scenarios=scenarios, simulations=simulations, contrarian=contrarian, evidence=evidence)
    assert first.model_dump() == second.model_dump()


def test_calculation_outputs_remain_calculation_provenance():
    _, proforma, _, simulations, _, _ = analytical_fixture()
    assert proforma.output_types["unlevered_irr"] == "CALCULATION"
    assert simulations[0].output_types["probability_loss"] == "CALCULATION"
    result = synthesize_investment_case(case_identity="case-1", proforma=proforma, simulations=simulations)
    assert result.output_type == "INTERPRETATION"
    assert result.provenance["layers"] == ["EVIDENCE", "AGENT_REASONING", "PRO_FORMA", "SCENARIO", "SIMULATION", "CONTRARIAN"]


def test_synthesis_does_not_change_workflow_or_create_authorization():
    service = WorkflowService()
    deal = service.create_deal(opportunity=Opportunity(name="test"))
    case = InvestmentCase(deal_id=deal.deal_id, workflow_state=deal.state)
    result = synthesize_investment_case(case_identity=deal.deal_id, proforma=calculate_proforma(base_input()))
    updated = apply_synthesis_to_case(case, result)
    assert updated.workflow_state == WorkflowState.DEAL_DISCOVERED
    assert service.get_deal(deal.deal_id).state == WorkflowState.DEAL_DISCOVERED
    assert service.authorizations(deal.deal_id) == []
    assert service.audit(deal.deal_id)[0]["event_type"] == "DEAL_CREATED"


def test_missing_scenario_or_simulation_does_not_invent_outputs():
    result = synthesize_investment_case(case_identity="case-1", proforma=calculate_proforma(base_input()))
    assert result.scenarios_reviewed == []
    assert result.simulations_reviewed == []
    assert result.contrarian_reviewed is False


def test_unresolved_disagreement_prevents_false_certainty():
    result = synthesize_investment_case(
        case_identity="case-1", proforma=calculate_proforma(base_input()),
        disagreements=[{"topic": "Exit assumptions", "status": "UNRESOLVED", "perspectives": ["investor", "contrarian"], "positions": ["supportive", "skeptical"], "unresolved_questions": ["What exit assumption is independently supported?"]}],
    )
    assert result.thesis_status == "CONDITIONAL"
    assert "What exit assumption is independently supported?" in result.unresolved_questions
