import pytest

from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner


def test_runner_delegates_to_contract_and_preserves_research_boundary():
    agent = DeterministicAgent(
        spec=AgentSpec("quant", "Quantitative Underwriting", "medium"),
        thesis="Test thesis",
        direction="NEUTRAL",
        confidence=0.5,
    )
    result = AgentRunner().run(
        agent,
        "Test question",
        [{"evidence_id": "E1", "source": "test", "claim": "usable evidence"}],
    )
    assert result["agent_id"] == "quant"
    assert result["provider"] == "contract"
    assert result["agent_runner"] == "AgentRunner"
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False
    assert result["human_decision_required"] is True


def test_runner_rejects_execution_capability_even_if_provider_is_custom():
    agent = DeterministicAgent(
        spec=AgentSpec(
            "unsafe",
            "Unsafe",
            "medium",
            capability_profile={
                "read_evidence": True,
                "reason": True,
                "execute": True,
                "brokerage": False,
                "portfolio_mutation": False,
            },
        ),
        thesis="Test thesis",
    )
    with pytest.raises(ValueError, match="execution capability"):
        AgentRunner().run(agent, "Test question", [])


def test_runner_rejects_brokerage_capability():
    agent = DeterministicAgent(
        spec=AgentSpec(
            "broker",
            "Brokerage",
            "medium",
            capability_profile={
                "read_evidence": True,
                "reason": True,
                "execute": False,
                "brokerage": True,
                "portfolio_mutation": False,
            },
        ),
        thesis="Test thesis",
    )
    with pytest.raises(ValueError, match="brokerage capability"):
        AgentRunner().run(agent, "Test question", [])
