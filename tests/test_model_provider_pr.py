from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_callable_provider_smoke():
    agent = DeterministicAgent(spec=AgentSpec("quant", "Quantitative Underwriting", "medium"))
    provider = CallableModelProvider(lambda p: {"agent_id": p["agent_id"]}, name="fixture")
    result = AgentRunner(provider).run(agent, "Question", [])
    assert result["provider"] == "fixture"
    assert result["human_decision_required"] is True
    assert result["execution_capability"] is False
