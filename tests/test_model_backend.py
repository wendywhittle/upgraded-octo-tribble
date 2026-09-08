import pytest

from app.agent_registry import build_default_registry
from app.model_backend import CallableModelBackend, CallableModelProvider, ModelBackendError


def test_backend_passes_structured_context_and_model_metadata():
    captured = {}

    def invoke(context):
        captured.update(context)
        return {"direction": "NEUTRAL", "confidence": 0.4, "thesis": "test"}

    agent = build_default_registry().get("quant")
    result = CallableModelBackend(invoke, model_name="test-model").assess(
        agent, "Assess the question", [{"evidence_id": "E1", "claim": "fact", "decision_usable": True}]
    )

    assert captured["question"] == "Assess the question"
    assert captured["agent"]["agent_id"] == "quant"
    assert captured["constraints"]["research_only"] is True
    assert captured["constraints"]["execution_capability"] is False
    assert result["model_version"] == "test-model"


def test_backend_rejects_non_mapping_output():
    agent = build_default_registry().get("researcher")
    backend = CallableModelBackend(lambda context: ["bad"])
    with pytest.raises(ModelBackendError):
        backend.assess(agent, "q", [])


def test_provider_wraps_backend():
    provider = CallableModelProvider(
        lambda context: {"direction": "NEUTRAL", "confidence": 0.1, "thesis": "ok"},
        model_name="provider-test",
    )
    agent = build_default_registry().get("investor")
    result = provider.assess(agent, "q", [])
    assert result["model_version"] == "provider-test"
