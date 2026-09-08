from app.agent_registry import build_default_registry
from app.agent_runner import AgentRunner
from app.model_backend import CallableModelProvider


def test_callable_model_provider_passes_through_runner_validation():
    calls = []

    def invoke(context):
        calls.append(context["agent"]["agent_id"])
        return {"direction": "NEUTRAL", "confidence": 0.5, "thesis": "model assessment"}

    provider = CallableModelProvider(invoke, model_name="integration-model")
    runner = AgentRunner(provider=provider)
    registry = build_default_registry()

    results = [runner.run(registry.get(agent_id), "test question", []) for agent_id in registry.ids()]

    assert calls == registry.ids()
    assert len(results) == 10
    assert all(item["model_version"] == "integration-model" for item in results)
    assert all(item["execution_capability"] is False for item in results)
    assert all(item["brokerage_connectivity"] is False for item in results)
    assert all(item["portfolio_mutation"] is False for item in results)
    assert all(item["human_decision_required"] is True for item in results)
