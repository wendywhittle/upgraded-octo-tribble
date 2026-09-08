from app.model_backend import CallableModelProvider
from app.agent_runner import AgentRunner


def test_model_backend_receives_institutional_learning_context():
    captured = {}

    def invoke(context):
        captured.update(context)
        return {
            "direction": "NEUTRAL",
            "confidence": 0.7,
            "horizon": "medium",
            "predicted_probability": 0.6,
        }

    runner = AgentRunner(CallableModelProvider(invoke, model_name="test-model"))
    agent = __import__("app.agent_registry", fromlist=["build_default_registry"]).build_default_registry().get("quant")
    learning = {
        "resolved_prediction_count": 4,
        "lessons": [{"type": "overconfidence", "agent_id": "quant"}],
        "informational_only": True,
    }

    result = runner.run(agent, "Does the signal persist?", [], learning_context=learning)

    assert captured["institutional_learning"] == learning
    assert result["learning_context_used"] is True
    assert result["human_decision_required"] is True
    assert result["execution_capability"] is False


def test_agent_runner_accepts_no_learning_context():
    def invoke(context):
        return {
            "direction": "NEUTRAL",
            "confidence": 0.5,
            "horizon": "medium",
        }

    runner = AgentRunner(CallableModelProvider(invoke, model_name="test-model"))
    agent = __import__("app.agent_registry", fromlist=["build_default_registry"]).build_default_registry().get("quant")
    result = runner.run(agent, "Baseline question", [])

    assert result["learning_context_used"] is False
