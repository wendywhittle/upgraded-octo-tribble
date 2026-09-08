from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_runner_reasserts_safety_flags():
    agent = DeterministicAgent(spec=AgentSpec("q", "Quant", "medium"))
    result = AgentRunner(CallableModelProvider(lambda p: {"execute": True}, "fixture")).run(agent, "Q", [])
    assert result["execution_capability"] is False
