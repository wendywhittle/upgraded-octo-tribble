from datetime import datetime, timezone

from app.evidence_orchestration import run_evidence_fed_agents


NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def test_custom_provider_runs_after_evidence_gate():
    calls = []

    class Provider:
        name = "fixture-model"

        def assess(self, agent, question, evidence):
            evidence = list(evidence)
            calls.append((agent.spec.agent_id, evidence))
            return {"agent_id": agent.spec.agent_id, "direction": "NEUTRAL", "confidence": 0.5}

    evidence = [{
        "evidence_id": "E1",
        "source": "fixture",
        "claim": "Validated observation",
        "observed_at": "2026-09-08T11:00:00+00:00",
        "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary"},
        "point_in_time": True,
    }]

    result = run_evidence_fed_agents("Assess the question", evidence, now=NOW, provider=Provider())
    assert result["provider"] == "fixture-model"
    assert len(calls) == 10
    assert all(items[0]["evidence_id"] == "E1" for _, items in calls)
    assert all(agent["execution_capability"] is False for agent in result["agents"])
