import pytest

from app.agent_registry import build_default_registry
from app.model_backend import CallableModelBackend, CallableModelProvider, ModelBackendError, OpenAIResponsesModelBackend
from app.model_provider import ResearcherOnlyModelProvider


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


def test_scientist_has_distinct_role_specific_prompt():
    registry = build_default_registry()
    scientist_prompt = OpenAIResponsesModelBackend._prompt(
        registry.get("scientist"),
        "Assess the opportunity",
        [{"evidence_id": "E1", "claim": "fact"}],
        {},
    )
    researcher_prompt = OpenAIResponsesModelBackend._prompt(
        registry.get("researcher"),
        "Assess the opportunity",
        [{"evidence_id": "E1", "claim": "fact"}],
        {},
    )

    assert "You are the Scientist perspective in AletheiaTelos." in scientist_prompt
    assert "What would have to be true for this conclusion to be valid, and what evidence could prove it wrong?" in scientist_prompt
    assert "confounding" in scientist_prompt
    assert "falsification" in scientist_prompt
    assert "You are the Researcher perspective in AletheiaTelos." in researcher_prompt
    assert "You are the Scientist perspective in AletheiaTelos." not in researcher_prompt
    assert scientist_prompt != researcher_prompt


def test_governance_has_distinct_role_specific_prompt():
    governance = OpenAIResponsesModelBackend._prompt(
        build_default_registry().get("governance"),
        "Assess the opportunity",
        [{"evidence_id": "E1", "claim": "fact"}],
        {},
    )

    assert "You are the Governance perspective in AletheiaTelos." in governance
    assert "CHARTER" in governance
    assert "human investment authority" in governance
    assert "autonomous execution" in governance
    assert "portfolio mutation" in governance
    assert "capital movement" in governance
    assert "evidence validation and provenance" in governance
    assert "immediate human review" in governance
    assert "Do not override other perspectives or make an investment decision." in governance


def test_selective_provider_routes_researcher_scientist_and_governance_only():
    class SpyProvider:
        name = "spy"

        def __init__(self):
            self.calls = []

        def assess(self, agent, question, evidence, learning_context=None):
            self.calls.append(agent.spec.agent_id)
            return {"direction": "NO_DATA", "confidence": 0.0, "horizon": agent.spec.default_horizon, "thesis": "ok", "evidence_basis": [], "contradictory_evidence_basis": [], "invalidation_conditions": [], "assumptions": []}

    researcher_provider = SpyProvider()
    scientist_provider = SpyProvider()
    governance_provider = SpyProvider()
    fallback = SpyProvider()
    provider = ResearcherOnlyModelProvider(
        researcher_provider,
        fallback=fallback,
        scientist_provider=scientist_provider,
        governance_provider=governance_provider,
    )
    registry = build_default_registry()

    provider.assess(registry.get("researcher"), "q", [])
    provider.assess(registry.get("scientist"), "q", [])
    provider.assess(registry.get("governance"), "q", [])
    provider.assess(registry.get("quant"), "q", [])

    assert researcher_provider.calls == ["researcher"]
    assert scientist_provider.calls == ["scientist"]
    assert governance_provider.calls == ["governance"]
    assert fallback.calls == ["quant"]


def test_scientist_uses_deterministic_fallback_without_real_model():
    scientist = build_default_registry().get("scientist")
    result = scientist.assess("q", [{"evidence_id": "E1", "claim": "fact"}])

    assert result["agent_id"] == "scientist"
    assert result["strategy"] == "Scientific and Epistemic Validity"
    assert result["capability_profile"]["execute"] is False
    assert result["capability_profile"]["brokerage"] is False
    assert result["capability_profile"]["portfolio_mutation"] is False
