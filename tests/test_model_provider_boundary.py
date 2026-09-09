import pytest

from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner


class FakeProvider:
    name = "fake"

    def assess(self, agent, question, evidence):
        return {
            "agent_id": agent.spec.agent_id,
            "strategy": agent.spec.role,
            "direction": "NEUTRAL",
            "confidence": 0.4,
            "horizon": agent.spec.default_horizon,
            "evidence": list(evidence),
            "model_version": "fake-1",
            "assumptions": ["Test only"],
            "invalidation_conditions": ["Test invalidation"],
        }


def test_custom_provider_is_replaceable_without_execution_capability():
    agent = DeterministicAgent(AgentSpec("quant", "Quantitative Underwriting", "medium"))
    result = AgentRunner(FakeProvider()).run(agent, "Assess", [])
    assert result["provider"] == "fake"
    assert result["model_version"] == "fake-1"
    assert result["human_decision_required"] is True
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False


def test_provider_output_must_satisfy_agent_contract():
    class InvalidProvider:
        name = "invalid"

        def assess(self, agent, question, evidence):
            return {"agent_id": agent.spec.agent_id, "direction": "INVALID"}

    agent = DeterministicAgent(AgentSpec("quant", "Quantitative Underwriting", "medium"))
    with pytest.raises(ValueError, match="invalid AgentOutput"):
        AgentRunner(InvalidProvider()).run(agent, "Assess", [])


def test_provider_cannot_grant_execution_authority():
    class EscalatingProvider(FakeProvider):
        def assess(self, agent, question, evidence):
            result = super().assess(agent, question, evidence)
            result.update({"execution_capability": True, "brokerage_connectivity": True, "portfolio_mutation": True})
            return result

    agent = DeterministicAgent(AgentSpec("quant", "Quantitative Underwriting", "medium"))
    with pytest.raises(ValueError, match="prohibited capability"):
        AgentRunner(EscalatingProvider()).run(agent, "Assess", [])
