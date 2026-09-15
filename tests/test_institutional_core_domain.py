from app.decision_gate import build_decision_gate
from app.decision_readiness import build_decision_readiness
from app.institutional_core import OpportunityStatus, build_opportunity
from app.institutional_investment_case import build_institutional_investment_case


def _simulation():
    return {
        "valid": True,
        "independent_of_agents": True,
        "scenarios": [
            {"scenario": "base"},
            {"scenario": "bull"},
            {"scenario": "bear"},
            {"scenario": "adversarial"},
        ],
    }


def _governance():
    return {
        "human_decision_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    }


def test_opportunity_is_not_evidence_and_can_exist_without_it():
    opportunity = build_opportunity(description="Candidate industrial acquisition")
    assert opportunity.status == OpportunityStatus.DISCOVERED
    assert opportunity.evidence_ids == []
    assert opportunity.to_dict()["evidence_validated"] is False


def test_opportunity_becomes_analysis_ready_only_when_usable_evidence_exists():
    opportunity = build_opportunity(description="Candidate security")
    assert opportunity.status == OpportunityStatus.DISCOVERED
    case = build_institutional_investment_case(
        "Should this be evaluated?",
        opportunity=opportunity.to_dict(),
        opportunity_id=opportunity.opportunity_id,
        evidence=[{"evidence_id": "E1", "source": "SEC", "provenance": {"uri": "x"}}],
        evidence_summary={"usable_count": 1, "validation": []},
        assumptions=["controlled assumption"],
        scenarios=_simulation()["scenarios"],
        risk=_simulation(),
        perspectives=[{"agent_id": "researcher", "evidence_basis": ["E1"]}],
        contrarian_review={"valid": True, "status": "reviewed", "challenges": ["challenge"]},
        synthesis={"verdict": "INVESTIGATE"},
        governance=_governance(),
    )
    readiness = build_decision_readiness(
        case,
        evidence={"usable_count": 1, "validation": []},
        simulation=_simulation(),
        skeptic={"valid": True, "status": "reviewed", "challenges": ["challenge"]},
        synthesis={"verdict": "INVESTIGATE"},
        governance=_governance(),
    )
    assert readiness["status"] == "NOT_READY"
    assert readiness["readiness_state"] == "CLOSED_BLOCKED"
    assert "THESIS_PRESENT" in readiness["hard_stops"]


def test_invalid_evidence_blocks_readiness():
    case = build_institutional_investment_case(
        "Evaluate candidate",
        evidence=[{"evidence_id": "E1", "source": "source", "provenance": {"uri": "x"}}],
        evidence_summary={"usable_count": 0, "validation": [{"decision_usable": False}]},
        governance=_governance(),
    )
    readiness = build_decision_readiness(
        case,
        evidence={"usable_count": 0, "validation": [{"decision_usable": False}]},
        simulation=_simulation(),
        skeptic={"valid": True, "status": "insufficient_data", "challenges": []},
        synthesis={"verdict": "NO_DATA"},
        governance=_governance(),
    )
    assert readiness["ready_for_human_authority"] is False
    assert "EVIDENCE_USABLE" in readiness["hard_stops"]
    assert readiness["authorized"] is False


def test_decision_gate_consumes_formal_readiness_without_authorizing():
    case = build_institutional_investment_case(
        "Evaluate candidate",
        evidence_summary={"usable_count": 0, "validation": []},
        governance=_governance(),
    )
    readiness = build_decision_readiness(
        case,
        evidence={"usable_count": 0, "validation": []},
        simulation=_simulation(),
        skeptic={"valid": True, "status": "insufficient_data", "challenges": []},
        synthesis={"verdict": "NO_DATA"},
        governance=_governance(),
    )
    gate = build_decision_gate(
        {"usable_count": 0, "validation": []},
        {"conflicts": [], "horizon_divergences": []},
        _simulation(),
        {"valid": True},
        {"verdict": "NO_DATA"},
        _governance(),
        decision_readiness=readiness,
    )
    assert gate["state"] == "CLOSED_BLOCKED"
    assert gate["human_authorization"] is None
    assert gate["approval"] is None
    assert gate["investment_authority"] is False


def test_case_identity_and_category_boundaries_are_explicit():
    case = build_institutional_investment_case(
        "Evaluate candidate",
        opportunity={"opportunity_id": "OPP-1"},
        opportunity_id="OPP-1",
        assumptions=["assumption"],
        calculations={"value": 1},
        scenarios=[{"scenario": "base"}],
        risk=_simulation(),
        governance=_governance(),
    )
    payload = case.to_dict()
    assert payload["investment_case_id"] == payload["case_id"]
    assert payload["opportunity_id"] == "OPP-1"
    assert payload["assumptions"] == ["assumption"]
    assert payload["calculations"] == {"value": 1}
    assert payload["scenarios"] == [{"scenario": "base"}]
    assert payload["risk"]["independent_of_agents"] is True
    assert payload["authorized"] is False
    assert payload["executed"] is False
