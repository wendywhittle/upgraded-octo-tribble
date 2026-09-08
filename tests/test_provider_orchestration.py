from datetime import datetime, timezone

from app.evidence_orchestration import run_evidence_fed_agents


NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


class RecordingProvider:
    name = "recording"

    def __init__(self):
        self.calls = []

    def assess(self, agent, question, evidence):
        evidence = list(evidence)
        self.calls.append((agent.spec.agent_id, question, evidence))
        return {
            "agent_id": agent.spec.agent_id,
            "strategy": agent.spec.role,
            "direction": "NEUTRAL",
            "confidence": 0.4,
            "horizon": agent.spec.default_horizon,
            "evidence": evidence,
            "model_version": "recording-1",
            "assumptions": ["Test provider"],
            "invalidation_conditions": ["Test invalidation"],
        }


def valid_evidence():
    return [{
        "evidence_id": "E-1",
        "source": "unit-test",
        "claim": "Observed condition is material.",
        "observed_at": "2026-09-08T11:00:00+00:00",
        "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
    }]


def test_evidence_orchestration_uses_injected_provider_for_every_perspective():
    provider = RecordingProvider()
    result = run_evidence_fed_agents(
        "Assess the opportunity",
        valid_evidence(),
        now=NOW,
        provider=provider,
    )
    assert result["provider"] == "recording"
    assert len(provider.calls) == 10
    assert all(call[2] for call in provider.calls)
    assert all(agent["provider"] == "recording" for agent in result["agents"])


def test_invalid_evidence_never_reaches_provider():
    provider = RecordingProvider()
    result = run_evidence_fed_agents(
        "Assess the opportunity",
        [{"evidence_id": "bad", "source": "unit-test", "claim": "Future claim", "observed_at": "2027-01-01T00:00:00+00:00"}],
        now=NOW,
        provider=provider,
    )
    assert result["usable_evidence_count"] == 0
    assert all(not call[2] for call in provider.calls)
