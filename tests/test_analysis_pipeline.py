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
    assert len(result["agents"]) == 10
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])
    assert result["synthesis"]["verdict"] == "NO_DATA"
    assert result["audit"]["simulation_independent_of_agents"] is True
    assert result["governance"]["human_decision_required"] is True


def test_full_pipeline_feeds_only_validated_evidence_to_agents():
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", evidence(), now=NOW, paths=100)
    assert result["evidence"]["count"] == 1
    assert result["evidence"]["usable_count"] == 1
    assert len(result["agents"]) == 10
    assert all(agent["evidence"] for agent in result["agents"])
    assert result["simulation"]["independent_of_agents"] is True
    assert result["governance"]["autonomous_execution"] is False


def test_full_pipeline_blocks_stale_evidence():
    stale = evidence()
    stale[0]["observed_at"] = "2020-01-01T00:00:00+00:00"
    with patch("app.analysis_pipeline.append_record"):
        result = run_analysis("Assess the opportunity", stale, now=NOW, max_age_seconds=60, paths=100)
    assert result["evidence"]["usable_count"] == 0
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])
