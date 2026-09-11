from datetime import datetime, timezone

import pytest

from app.investment_case import build_structured_investment_case


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def make_case(recommendation="INVESTIGATE"):
    return build_structured_investment_case(
        question="Assess the opportunity",
        evidence={
            "count": 1,
            "usable_count": 1,
            "validation": [],
            "items": [{"evidence_id": "E-1", "source": "primary-source", "claim": "Material demand exists."}],
        },
        agents=[{
            "agent_id": "quant",
            "direction": "LONG",
            "confidence": 0.7,
            "assumptions": ["Demand persists."],
            "evidence": ["E-1"],
        }],
        simulation={
            "engine": "independent",
            "independent_of_agents": True,
            "scenarios": [
                {"scenario": "base", "probability_loss": 0.2},
                {"scenario": "bear", "probability_loss": 0.6},
                {"scenario": "adversarial", "probability_loss": 0.8},
            ],
        },
        skeptic={"recommendation": "hold", "challenges": ["Downside is material."]},
        synthesis={"verdict": recommendation, "unresolved_questions": ["What invalidates the thesis?"]},
        meta_intelligence={"reasoning_health": "ADEQUATE"},
        created_at=NOW,
    )


def test_case_converges_upstream_artifacts_and_preserves_provenance():
    case = make_case()
    assert case.evidence_refs[0].ref_id == "E-1"
    assert case.evidence_refs[0].source == "primary-source"
    assert case.independent_reasoning[0]["agent_id"] == "quant"
    assert case.validated_assumptions == ["Demand persists."]
    assert case.simulation["independent_of_agents"] is True
    assert case.contrarian_review["recommendation"] == "hold"
    assert "Capital stack is not present" in " ".join(case.gaps)
    assert "Lender evidence is not present" in " ".join(case.gaps)


def test_case_is_immutable_and_gate_is_not_authorization():
    case = make_case()
    with pytest.raises(Exception):
        case.recommendation = "NO_GO"
    assert case.human_decision_gate.required is True
    assert case.human_decision_gate.status == "pending"
    assert case.human_decision_gate.authorized is False
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False


def test_case_preserves_scenario_distribution_and_supports_no_go():
    case = make_case("NO_GO")
    assert case.recommendation == "HOLD"  # skeptic hold remains authoritative in this boundary
    assert {item["scenario"] for item in case.scenarios} == {"base", "bear", "adversarial"}
    payload = case.model_dump(mode="json")
    assert payload["human_decision_gate"]["status"] == "pending"
    assert payload["authority"] == "none"


def test_missing_components_are_gaps_not_fabricated_outputs():
    case = build_structured_investment_case(
        question="Assess incomplete opportunity",
        evidence={"count": 0, "usable_count": 0, "validation": [], "items": []},
        agents=[],
        simulation={"independent_of_agents": True, "scenarios": []},
        skeptic={"recommendation": "hold", "challenges": []},
        synthesis={"verdict": "NO_DATA", "unresolved_questions": []},
        created_at=NOW,
    )
    assert case.pro_forma is None
    assert case.capital_stack is None
    assert case.lender_evidence == []
    assert any("pro forma" in gap.lower() for gap in case.gaps)
    assert any("capital stack" in gap.lower() for gap in case.gaps)
    assert any("lender evidence" in gap.lower() for gap in case.gaps)
