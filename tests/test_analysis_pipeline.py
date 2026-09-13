from datetime import datetime, timezone
from unittest.mock import patch

from app.analysis_pipeline import run_analysis


NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def evidence(claim="The observed condition is material."):
    return [{
        "evidence_id": "E-1",
        "source": "unit-test-source",
        "claim": claim,
        "observed_at": "2026-09-08T11:00:00+00:00",
        "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
    }]


def test_full_pipeline_preserves_no_data_without_evidence():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", [], now=NOW, paths=100)
    assert result["evidence"]["usable_count"] == 0
    assert len(result["agents"]) == 8
    assert len(result["active_perspectives"]) == 9
    assert result["active_perspectives"] == ["researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance", "observer"]
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])
    assert result["synthesis"]["verdict"] == "NO_DATA"
    assert result["meta_intelligence"]["reasoning_health"] == "INSUFFICIENT"
    assert result["meta_intelligence"]["directional_vote"] is None
    assert result["audit"]["simulation_independent_of_agents"] is True
    assert result["audit"]["meta_intelligence_directional_vote"] is False
    assert result["governance"]["human_decision_required"] is True
    assert result["kaleidoscope"]["read_only"] is True
    assert result["kaleidoscope"]["perspective_count"] == 8
    assert result["kaleidoscope"]["expected_perspective_count"] == 9
    assert result["kaleidoscope"]["meta_intelligence"]["reasoning_health"] == "INSUFFICIENT"


def test_full_pipeline_feeds_only_validated_evidence_to_active_reasoning_agents():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", evidence(), now=NOW, paths=100)
    assert result["evidence"]["count"] == 1
    assert result["evidence"]["usable_count"] == 1
    assert len(result["agents"]) == 8
    assert {agent["agent_id"] for agent in result["agents"]} == {"researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance"}
    assert all(agent["evidence"] for agent in result["agents"])
    assert all(agent["execution_capability"] is False for agent in result["agents"])
    assert all(agent["brokerage_connectivity"] is False for agent in result["agents"])
    assert all(agent["portfolio_mutation"] is False for agent in result["agents"])
    assert result["simulation"]["independent_of_agents"] is True
    assert result["governance"]["human_decision_required"] is True
    assert result["governance"]["autonomous_execution"] is False
    assert result["governance"]["brokerage_connectivity"] is False
    assert result["governance"]["portfolio_mutation"] is False
    assert result["kaleidoscope"]["expected_perspective_count"] == 9
    assert result["kaleidoscope"]["human_decision_required"] is True
    assert result["kaleidoscope"]["execution_capability"] is False
    assert result["kaleidoscope"]["brokerage_connectivity"] is False
    assert result["kaleidoscope"]["portfolio_mutation"] is False
    assert result["audit"]["perspectives_share_conclusions"] is False
    assert result["meta_intelligence"]["directional_vote"] is None
    assert result["meta_intelligence"]["execution_capability"] is False


def test_full_pipeline_blocks_stale_evidence():
    stale = evidence()
    stale[0]["observed_at"] = "2020-01-01T00:00:00+00:00"
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", stale, now=NOW, max_age_seconds=60, paths=100)
    assert result["evidence"]["usable_count"] == 0
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])


def test_full_pipeline_surfaces_meta_intelligence_before_synthesis():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", evidence(), now=NOW, paths=100)
    meta = result["meta_intelligence"]
    assert meta["status"] == "evaluated"
    assert "recommended_next_step" in meta
    assert "meta_intelligence" in result["synthesis"]
    assert result["synthesis"]["meta_intelligence"] == meta


def test_analysis_pipeline_does_not_create_decision_record_without_human_input():
    with patch("app.analysis_pipeline.append_record"), patch("app.decision_record.build_decision_record") as build_decision_record:
        result = run_analysis("Assess the opportunity", evidence(), now=NOW, paths=100)

    build_decision_record.assert_not_called()
    assert result["decision_gate"]["human_decision"] is None
    assert result["decision_gate"]["human_authorization"] is None
    assert result["decision_gate"]["investment_authority"] is False
    assert result["institutional_investment_case"]["decision_record_ref"] is None


def test_ready_gate_is_not_human_authorization():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", evidence(), now=NOW, paths=100)

    assert result["decision_readiness"]["status"] == "READY_FOR_HUMAN_AUTHORITY"
    assert result["decision_readiness"]["authorized"] is False
    assert result["decision_readiness"]["human_authorization"] is None
    assert result["decision_gate"]["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert result["decision_gate"]["human_authorization"] is None
    assert result["decision_gate"]["approval"] is None
    assert result["decision_gate"]["investment_authority"] is False
