import pytest

from app.agent_contract import AgentRegistry, AgentSpec, DeterministicAgent


EVIDENCE = [
    {
        "evidence_id": "E1",
        "source": "test-source",
        "claim": "The supplied observation supports the research question.",
        "observed_at": "2026-09-08T15:00:00+00:00",
        "retrieved_at": "2026-09-08T15:05:00+00:00",
        "provenance": {"type": "test", "point_in_time": True},
        "decision_usable": True,
    }
]


def make_agent(agent_id="quant"):
    return DeterministicAgent(
        spec=AgentSpec(agent_id, "Quantitative Underwriting", "medium"),
        direction="LONG",
        confidence=0.7,
        thesis="The supplied evidence supports the thesis.",
    )


def test_agent_assessment_satisfies_contract():
    result = make_agent().assess("Is the thesis supported?", EVIDENCE)
    assert result["agent_id"] == "quant"
    assert result["direction"] == "LONG"
    assert result["confidence"] == 0.7
    assert result["strategy"] == "Quantitative Underwriting"
    assert result["capability_profile"]["execute"] is False
    assert result["capability_profile"]["brokerage"] is False
    assert result["human_decision_required"] is True


def test_blocked_evidence_produces_no_data():
    blocked = [{**EVIDENCE[0], "decision_usable": False}]
    result = make_agent().assess("Question", blocked)
    assert result["direction"] == "NO_DATA"
    assert result["confidence"] == 0.0
    assert result["evidence"] == []


def test_registry_runs_agents_and_preserves_ids():
    registry = AgentRegistry([make_agent("quant"), make_agent("researcher")])
    results = registry.run_all("Question", {"quant": EVIDENCE, "researcher": EVIDENCE})
    assert registry.ids() == ["quant", "researcher"]
    assert [item["agent_id"] for item in results] == ["quant", "researcher"]


def test_registry_rejects_execution_capability():
    spec = AgentSpec(
        "unsafe",
        "Unsafe",
        "medium",
        {"read_evidence": True, "reason": True, "execute": True, "brokerage": False, "portfolio_mutation": False},
    )
    with pytest.raises(ValueError, match="execution capability"):
        AgentRegistry([DeterministicAgent(spec, thesis="x")])


def test_registry_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="Duplicate agent_id"):
        AgentRegistry([make_agent(), make_agent()])
