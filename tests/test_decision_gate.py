from datetime import datetime, timezone
from unittest.mock import patch

from app.analysis_pipeline import run_analysis
from app.decision_gate import DecisionGateState, build_decision_gate


NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def simulation():
    return {"valid": True, "independent_of_agents": True, "scenarios": [{"scenario": "base"}, {"scenario": "bull"}, {"scenario": "bear"}, {"scenario": "adversarial"}]}


def skeptic():
    return {"valid": True, "status": "reviewed", "recommendation": "proceed_to_synthesis", "challenges": ["Test challenge"]}


def synthesis(verdict="CONDITIONAL GO"):
    return {"verdict": verdict}


def governance():
    return {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False, "investment_authority": False}


def test_ready_gate_is_not_human_authorization_direct_builder():
    gate = build_decision_gate(
        {"usable_count": 1, "validation": []}, {"conflicts": [], "horizon_divergences": []}, simulation(), skeptic(), synthesis(), governance(), "present",
    )
    assert gate["ready_for_human_authority"] is True
    assert gate["approval"] is None
    assert gate["human_authorization"] is None
    assert gate["autonomous_execution"] is False
    assert gate["brokerage_connectivity"] is False
    assert gate["portfolio_mutation"] is False
    assert gate["investment_authority"] is False


def test_pipeline_exposes_gate_without_populating_human_decision():
    evidence = [{
        "evidence_id": "E-1", "source": "unit-test-source", "claim": "The observed condition is material.",
        "observed_at": "2026-09-08T11:00:00+00:00", "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
    }]
    with patch("app.analysis_pipeline.append_record") as append:
        result = run_analysis(
            "Assess the opportunity", evidence,
            thesis={"statement": "Explicit test thesis."},
            assumptions=["Explicit test assumption."], calculations={"value": 101.0}, now=NOW, paths=20,
        )
    assert result["decision_gate"]["state"] == DecisionGateState.OPEN_READY_FOR_HUMAN_AUTHORITY.value
    assert result["decision_gate"]["human_decision"] is None
    assert result["decision_gate"]["human_authorization"] is None
    assert result["governance"]["autonomous_execution"] is False
    assert result["governance"]["brokerage_connectivity"] is False
    assert result["governance"]["portfolio_mutation"] is False
    record = append.call_args.args[0]
    assert record["system_synthesis"] == result["synthesis"]
    assert record["decision_gate"] == result["decision_gate"]
    assert record["human_decision"] is None
    assert record["human_authorization"] is None
    assert record["audit"]["reconstructable"] is True
    assert record["audit"]["simulation_seed"] == 42
