from app.agent_registry import build_default_registry
from app.agent_runner import AgentRunner


def test_explicit_probability_gets_stable_prediction_id():
    agent = build_default_registry().get("quant")

    class Provider:
        name = "test-model"

        def assess(self, agent, question, evidence):
            return {
                "direction": "LONG",
                "confidence": 0.7,
                "predicted_probability": 0.8,
                "model_version": "test-1",
                "evidence": [],
                "assumptions": [],
                "invalidation_conditions": [],
            }

    evidence = [{"evidence_id": "E-1"}]
    first = AgentRunner(Provider()).run(agent, "Will the thesis hold?", evidence)
    second = AgentRunner(Provider()).run(agent, "Will the thesis hold?", evidence)
    assert first["prediction_id"] == second["prediction_id"]
    assert first["predicted_probability"] == 0.8


def test_changed_evidence_context_creates_new_prediction_id():
    agent = build_default_registry().get("quant")

    class Provider:
        name = "test-model"

        def assess(self, agent, question, evidence):
            return {"direction": "LONG", "confidence": 0.7, "predicted_probability": 0.8, "model_version": "test-1"}

    runner = AgentRunner(Provider())
    first = runner.run(agent, "Question", [{"evidence_id": "E-1"}])
    second = runner.run(agent, "Question", [{"evidence_id": "E-2"}])
    assert first["prediction_id"] != second["prediction_id"]


def test_confidence_alone_does_not_create_prediction_id():
    agent = build_default_registry().get("quant")

    class Provider:
        name = "test-model"

        def assess(self, agent, question, evidence):
            return {"direction": "LONG", "confidence": 0.9, "model_version": "test-1"}

    result = AgentRunner(Provider()).run(agent, "Question", [])
    assert result["prediction_id"] is None
