from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_provider_cannot_grant_execution():
    agent = DeterministicAgent(spec=AgentSpec("systems", "Systems Risk", "medium"))
    provider = CallableModelProvider(lambda p: {"execute": True}, name="fixture")
    result = AgentRunner(provider).run(agent, "Question", [])
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False
