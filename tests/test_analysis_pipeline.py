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
        result = run_analysis(
            "Assess the opportunity",
            evidence(),
            thesis={"statement": "Explicit test thesis."},
            assumptions=["Explicit test assumption."],
            calculations={"value": 101.0},
            now=NOW,
            paths=100,
        )

    assert result["decision_readiness"]["status"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert result["decision_readiness"]["authorized"] is False
    assert result["decision_readiness"]["human_authorization"] is None
    assert result["decision_gate"]["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert result["decision_gate"]["human_authorization"] is None
    assert result["decision_gate"]["approval"] is None
    assert result["decision_gate"]["investment_authority"] is False
