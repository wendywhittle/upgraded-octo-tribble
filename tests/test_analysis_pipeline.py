from datetime import datetime, timezone

from app.analysis_pipeline import run_analysis


NOW = datetime(2026, 9, 8, 17, 0, tzinfo=timezone.utc)


def evidence(claim="Revenue growth is improving"):
    return {
        "evidence_id": "E1",
        "source": "test-source",
        "claim": claim,
        "observed_at": "2026-09-08T16:00:00+00:00",
        "retrieved_at": "2026-09-08T16:30:00+00:00",
        "provenance": {"type": "test", "point_in_time": True},
    }


def test_full_pipeline_preserves_order_and_boundaries():
    result = run_analysis(
        question="Is the opportunity worth further investigation?",
        evidence=[evidence()],
        initial_value=100,
        horizon_steps=5,
        paths=100,
        seed=7,
        now=NOW,
        max_age_seconds=86400,
    )

    assert result["evidence"]["usable_count"] == 1
    assert len(result["agents"]) == 10
    assert result["audit"]["simulation_independent_of_agents"] is True
    assert result["governance"]["human_decision_required"] is True
    assert result["governance"]["autonomous_execution"] is False
    assert result["governance"]["brokerage_connectivity"] is False
    assert result["governance"]["portfolio_mutation"] is False
    assert result["audit"]["memory_recorded"] is True


def test_full_pipeline_blocks_future_evidence():
    future = dict(evidence())
    future["observed_at"] = "2026-09-08T18:00:00+00:00"
    result = run_analysis(
        question="Test future evidence",
        evidence=[future],
        horizon_steps=2,
        paths=100,
        now=NOW,
    )

    assert result["evidence"]["usable_count"] == 0
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])


def test_full_pipeline_is_reproducible_for_same_seed():
    first = run_analysis("Reproducibility", [evidence()], horizon_steps=3, paths=100, seed=99, now=NOW)
    second = run_analysis("Reproducibility", [evidence()], horizon_steps=3, paths=100, seed=99, now=NOW)
    assert first["simulation"] == second["simulation"]
