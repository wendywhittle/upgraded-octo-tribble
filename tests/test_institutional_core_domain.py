from datetime import datetime, timedelta, timezone

import pytest

from app.decision_gate import build_decision_gate
from app.decision_readiness import build_decision_readiness
from app.decision_record import HumanDecision, build_decision_record
from app.evidence import validate_evidence
from app.institutional_core import OpportunityStatus, build_opportunity
from app.institutional_investment_case import build_institutional_investment_case
from app.simulator import run_monte_carlo


def simulation():
    return {"simulation_id": "SIM-1", "valid": True, "independent_of_agents": True, "scenarios": [{"scenario": "base"}, {"scenario": "bull"}, {"scenario": "bear"}, {"scenario": "adversarial"}]}


def governance():
    return {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False, "investment_authority": False}


def valid_evidence(evidence_id="E1", source="SEC"):
    return {"evidence_id": evidence_id, "source": source, "claim": "A documented institutional fact", "provenance": {"uri": "https://example.test/source", "publisher": source, "point_in_time": True}, "retrieved_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()}


def ready_case(**overrides):
    perspectives = ["researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance"]
    values = {
        "question": "Evaluate candidate", "opportunity": {"opportunity_id": "OPP-1"}, "opportunity_id": "OPP-1",
        "evidence": [valid_evidence()], "evidence_summary": {"usable_count": 1, "validation": []},
        "thesis": {"statement": "The risk-adjusted case is attractive if the documented assumptions hold."},
        "assumptions": ["Explicit underwriting assumption"], "calculations": {"method": "deterministic", "value": 101.0},
        "scenarios": simulation()["scenarios"], "risk": simulation(),
        "perspectives": [{"agent_id": p, "evidence_basis": ["E1"]} for p in perspectives],
        "perspective_provenance": [{"agent_id": p, "independence": "shared_pipeline_inputs", "independence_limitation": "Separate identity does not prove model independence."} for p in perspectives],
        "contrarian_review": {"valid": True, "status": "reviewed", "challenges": ["Failure condition"]}, "governance": governance(),
    }
    values.update(overrides)
    return build_institutional_investment_case(**values)


def test_opportunity_can_exist_without_evidence():
    opportunity = build_opportunity(description="Candidate industrial acquisition")
    assert opportunity.status == OpportunityStatus.DISCOVERED
    assert opportunity.evidence_ids == []
    assert opportunity.to_dict()["evidence_validated"] is False


def test_invalid_evidence_blocks_readiness():
    case = build_institutional_investment_case("Evaluate candidate", evidence=[valid_evidence()], evidence_summary={"usable_count": 0, "validation": [{"decision_usable": False}]}, governance=governance())
    readiness = build_decision_readiness(case, evidence={"usable_count": 0, "validation": [{"decision_usable": False}]}, simulation=simulation(), skeptic={"valid": True, "status": "insufficient_data", "challenges": []}, synthesis={"verdict": "NO_DATA"}, governance=governance())
    assert readiness["ready_for_human_authority"] is False
    assert "EVIDENCE_USABLE" in readiness["hard_stops"]
    assert readiness["authorized"] is False


def test_readiness_requires_explicit_thesis():
    case = ready_case(thesis={})
    readiness = build_decision_readiness(case, evidence={"usable_count": 1, "validation": []}, simulation=simulation(), skeptic=case.contrarian_review, synthesis={"verdict": "INVESTIGATE"}, governance=governance())
    assert readiness["readiness_state"] == "CLOSED_BLOCKED"
    assert "THESIS_PRESENT" in readiness["hard_stops"]


def test_sufficient_package_is_ready_but_not_authorized():
    case = ready_case()
    readiness = build_decision_readiness(case, evidence={"usable_count": 1, "validation": []}, simulation=simulation(), skeptic=case.contrarian_review, synthesis={"verdict": "INVESTIGATE"}, governance=governance())
    assert readiness["status"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert readiness["authorized"] is False
    gate = build_decision_gate({"usable_count": 1, "validation": []}, {"conflicts": [], "horizon_divergences": []}, simulation(), case.contrarian_review, {"verdict": "INVESTIGATE"}, governance(), decision_readiness=readiness)
    assert gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert gate["human_authorization"] is None
    assert gate["investment_authority"] is False


def test_decision_gate_never_authorizes_blocked_case():
    case = build_institutional_investment_case("Evaluate candidate", evidence_summary={"usable_count": 0, "validation": []}, governance=governance())
    readiness = build_decision_readiness(case, evidence={"usable_count": 0, "validation": []}, simulation=simulation(), skeptic={"valid": True, "status": "insufficient_data", "challenges": []}, synthesis={"verdict": "NO_DATA"}, governance=governance())
    gate = build_decision_gate({"usable_count": 0, "validation": []}, {"conflicts": [], "horizon_divergences": []}, simulation(), {"valid": True}, {"verdict": "NO_DATA"}, governance(), decision_readiness=readiness)
    assert gate["state"] == "CLOSED_BLOCKED"
    assert gate["human_authorization"] is None
    assert gate["approval"] is None
    assert gate["investment_authority"] is False


def test_investment_case_has_canonical_identity_and_opportunity_link():
    case = ready_case()
    payload = case.to_dict()
    assert payload["investment_case_id"] == payload["case_id"]
    assert payload["opportunity_id"] == "OPP-1"
    assert payload["authorized"] is False
    assert payload["executed"] is False


def test_evidence_trust_boundary_cases():
    now = datetime.now(timezone.utc)
    assert validate_evidence(valid_evidence(), now=now)["decision_usable"] is True
    missing_id = valid_evidence(); missing_id.pop("evidence_id")
    assert validate_evidence(missing_id, now=now)["decision_usable"] is False
    missing_provenance = valid_evidence(); missing_provenance.pop("provenance")
    assert validate_evidence(missing_provenance, now=now)["decision_usable"] is False
    synthetic = valid_evidence(); synthetic["provenance"]["type"] = "synthetic_demo"
    assert validate_evidence(synthetic, now=now)["decision_usable"] is False
    stale = valid_evidence(); stale["retrieved_at"] = (now - timedelta(days=2)).isoformat()
    assert validate_evidence(stale, now=now, max_age_seconds=86400)["decision_usable"] is False


def test_simulation_contract_is_explicit_and_invalid_inputs_are_rejected():
    result = run_monte_carlo(initial_value=100, horizon_steps=2, paths=100, seed=1)
    assert result["simulation_id"].startswith("SIM-")
    assert result["valid"] is True
    assert result["methodology"]
    assert result["independent_of_agents"] is True
    assert {s["scenario"] for s in result["scenarios"]} == {"base", "bull", "bear", "adversarial"}
    with pytest.raises(ValueError):
        run_monte_carlo(initial_value=0, paths=100)
    with pytest.raises(ValueError):
        run_monte_carlo(initial_value=100, paths=0)


def test_missing_downside_cannot_satisfy_readiness():
    bad_sim = {**simulation(), "scenarios": [{"scenario": "base"}, {"scenario": "bull"}]}
    case = ready_case(scenarios=bad_sim["scenarios"], risk=bad_sim)
    readiness = build_decision_readiness(case, evidence={"usable_count": 1, "validation": []}, simulation=bad_sim, skeptic=case.contrarian_review, synthesis={"verdict": "INVESTIGATE"}, governance=governance())
    assert readiness["readiness_state"] == "CLOSED_BLOCKED"
    assert "DOWNSIDE_ADDRESSED" in readiness["hard_stops"]


def test_no_fake_conflict_is_created_by_empty_conflict_set():
    case = ready_case(conflicts={"conflicts": [], "horizon_divergences": []})
    readiness = build_decision_readiness(case, evidence={"usable_count": 1, "validation": []}, simulation=simulation(), skeptic=case.contrarian_review, synthesis={"verdict": "INVESTIGATE"}, governance=governance())
    assert readiness["readiness_state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert case.conflicts["conflicts"] == []


def test_decision_record_requires_explicit_human_input_and_is_frozen():
    now = datetime.now(timezone.utc)
    record = build_decision_record(
        decision_record_id="DR-1", opportunity_id="OPP-1", case_id="CASE-1", case_version=1, decided_at=now,
        decision_readiness_state="OPEN_READY_FOR_HUMAN_AUTHORITY", decision_gate_state="OPEN_READY_FOR_HUMAN_AUTHORITY",
        decision_gate_snapshot={"state": "OPEN_READY_FOR_HUMAN_AUTHORITY"}, investment_case_ref="CASE-1",
        decision=HumanDecision.GO, human_rationale="Human IC decision based on the recorded case.", decision_maker_role="Investment IC",
        authorized=False, evidence_refs=["E1"], analytical_artifact_refs=["SIM-1"],
    )
    assert record.authorized is False
    assert record.opportunity_id == "OPP-1"
    with pytest.raises(Exception):
        record.decision = HumanDecision.NO_GO
    with pytest.raises(ValueError):
        build_decision_record(
            decision_record_id="DR-2", opportunity_id="OPP-1", case_id="CASE-1", case_version=1,
            decided_at=now, decision_readiness_state="CLOSED_BLOCKED", decision_gate_state="CLOSED_BLOCKED",
            investment_case_ref="CASE-1", decision=HumanDecision.GO, human_rationale="x", decision_maker_role="Investment IC", authorized=False,
        )
