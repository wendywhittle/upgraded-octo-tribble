from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_provider_result_is_annotated_by_runner():
    agent = DeterministicAgent(spec=AgentSpec("researcher", "Fundamental Research", "medium"))
    provider = CallableModelProvider(
        lambda payload: {"agent_id": payload["agent_id"], "direction": "NO_DATA", "confidence": 0.0},
        name="fixture",
    )
    result = AgentRunner(provider).run(agent, "Question", [])
    assert result["provider"] == "fixture"
    assert result["human_decision_required"] is True
    assert result["execution_capability"] is False
