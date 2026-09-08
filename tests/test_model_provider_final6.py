import pytest
from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_provider_requires_structured_result():
    agent = DeterministicAgent(spec=AgentSpec("quant", "Quant", "medium"))
    with pytest.raises(TypeError):
        AgentRunner(CallableModelProvider(lambda p: [], name="fixture")).run(agent, "Q", [])
