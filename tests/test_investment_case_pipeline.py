from datetime import datetime, timezone
from unittest.mock import patch

from app.analysis_pipeline import run_analysis


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def test_pipeline_emits_structured_investment_case_before_human_gate():
    evidence = [{
        "evidence_id": "E-1",
        "source": "primary-source",
        "claim": "Material demand exists.",
        "observed_at": "2026-09-11T14:00:00+00:00",
        "retrieved_at": "2026-09-11T14:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
    }]
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", evidence, now=NOW, paths=100)

    case = result["structured_investment_case"]
    assert case["case_id"].startswith("investment-case:")
    assert case["evidence_refs"][0]["ref_id"] == "E-1"
    assert case["independent_reasoning"]
    assert case["scenarios"]
    assert case["simulation"]["independent_of_agents"] is True
    assert case["contrarian_review"] == result["skeptic"]
    assert case["synthesis"] == result["synthesis"]
    assert case["human_decision_gate"]["required"] is True
    assert case["human_decision_gate"]["status"] == "pending"
    assert case["human_decision_gate"]["authorized"] is False
    assert case["authority"] == "none"
    assert case["execution_capability"] is False
    assert case["portfolio_mutation"] is False
    assert result["audit"]["investment_case_is_authorization"] is False
    assert result["audit"]["human_decision_gate_pending"] is True


def test_pipeline_no_data_produces_valid_non_authorizing_case():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", [], now=NOW, paths=100)
    case = result["structured_investment_case"]
    assert case["recommendation"] == "NO_DATA"
    assert case["human_decision_gate"]["status"] == "pending"
    assert case["authority"] == "none"
    assert any("evidence" in gap.lower() for gap in case["gaps"])
