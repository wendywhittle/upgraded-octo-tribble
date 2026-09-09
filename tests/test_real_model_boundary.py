import json

import pytest

from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner
from app.model_backend import ModelBackendError, OpenAIResponsesModelBackend, build_default_model_provider
from app.model_provider import ContractModelProvider, ResearcherOnlyModelProvider


EVIDENCE = [
    {
        "evidence_id": "E1",
        "source": "test-source",
        "claim": "Observed condition supports the research question.",
        "observed_at": "2026-09-08T15:00:00+00:00",
        "retrieved_at": "2026-09-08T15:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
        "decision_usable": True,
    },
    {
        "evidence_id": "E2",
        "source": "test-source-2",
        "claim": "Observed condition introduces a material counterpoint.",
        "observed_at": "2026-09-08T15:00:00+00:00",
        "retrieved_at": "2026-09-08T15:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
        "decision_usable": True,
    },
]


def researcher():
    return DeterministicAgent(AgentSpec("researcher", "Evidence-Bound Fundamental Research", "medium"), thesis="deterministic fallback")


def fake_post(_url, _payload, _headers):
    return {
        "output_text": json.dumps(
            {
                "direction": "LONG",
                "confidence": 0.72,
                "horizon": "medium",
                "thesis": "E1 supports the thesis while E2 is a material counterpoint.",
                "evidence_basis": ["E1"],
                "contradictory_evidence_basis": ["E2"],
                "invalidation_conditions": ["E1 is shown to be unreliable."],
                "assumptions": ["The supplied evidence remains decision-usable."],
            }
        )
    }


def test_real_backend_returns_structured_provenance_bound_output():
    backend = OpenAIResponsesModelBackend(api_key="test-key", model_name="test-model", post_json=fake_post)
    result = backend.assess(researcher(), "Assess the thesis", EVIDENCE)
    assert result["direction"] == "LONG"
    assert result["evidence_basis"] == ["E1"]
    assert [item["evidence_id"] for item in result["evidence"]] == ["E1", "E2"]
    assert [item["evidence_id"] for item in result["contradictory_evidence"]] == ["E2"]
    assert result["model_version"] == "test-model"


def test_real_backend_rejects_malformed_structured_output():
    def malformed(_url, _payload, _headers):
        return {"output_text": "not-json"}

    backend = OpenAIResponsesModelBackend(api_key="test-key", post_json=malformed)
    with pytest.raises(ModelBackendError, match="non-JSON"):
        backend.assess(researcher(), "Assess", EVIDENCE)


def test_real_backend_rejects_unknown_evidence_id():
    def forged(_url, _payload, _headers):
        return {
            "output_text": json.dumps(
                {
                    "direction": "LONG",
                    "confidence": 0.7,
                    "horizon": "medium",
                    "thesis": "Unsupported.",
                    "evidence_basis": ["FORGED"],
                    "contradictory_evidence_basis": [],
                    "invalidation_conditions": [],
                    "assumptions": [],
                }
            )
        }

    backend = OpenAIResponsesModelBackend(api_key="test-key", post_json=forged)
    with pytest.raises(ModelBackendError, match="provenance"):
        backend.assess(researcher(), "Assess", EVIDENCE)


def test_real_backend_returns_no_data_without_evidence_and_does_not_call_model():
    called = False

    def should_not_call(_url, _payload, _headers):
        nonlocal called
        called = True
        return {}

    backend = OpenAIResponsesModelBackend(api_key="test-key", post_json=should_not_call)
    result = backend.assess(researcher(), "Assess", [])
    assert result["direction"] == "NO_DATA"
    assert result["confidence"] == 0.0
    assert called is False


def test_runner_rejects_model_authority_escalation():
    class UnsafeProvider:
        name = "unsafe"

        def assess(self, agent, question, evidence, learning_context=None):
            return {
                "agent_id": agent.spec.agent_id,
                "strategy": agent.spec.role,
                "direction": "NEUTRAL",
                "confidence": 0.0,
                "horizon": agent.spec.default_horizon,
                "model_version": "unsafe",
                "execution_capability": True,
            }

    with pytest.raises(ValueError, match="prohibited capability"):
        AgentRunner(UnsafeProvider()).run(researcher(), "Assess", EVIDENCE)


def test_runner_rejects_wrong_agent_identity():
    class WrongAgentProvider:
        name = "wrong"

        def assess(self, agent, question, evidence, learning_context=None):
            return {
                "agent_id": "quant",
                "strategy": agent.spec.role,
                "direction": "NEUTRAL",
                "confidence": 0.0,
                "horizon": agent.spec.default_horizon,
                "model_version": "wrong",
            }

    with pytest.raises(ValueError, match="wrong agent"):
        AgentRunner(WrongAgentProvider()).run(researcher(), "Assess", EVIDENCE)


def test_selective_provider_only_routes_researcher_to_real_provider():
    class RecordingProvider:
        name = "real-test"

        def __init__(self):
            self.calls = []

        def assess(self, agent, question, evidence, learning_context=None):
            self.calls.append(agent.spec.agent_id)
            return {
                "agent_id": agent.spec.agent_id,
                "strategy": agent.spec.role,
                "direction": "NEUTRAL",
                "confidence": 0.1,
                "horizon": agent.spec.default_horizon,
                "thesis": "Evidence-bound test result",
                "model_version": "test-model",
                "evidence": evidence,
            }

    real = RecordingProvider()
    provider = ResearcherOnlyModelProvider(real, fallback=ContractModelProvider())
    quant = DeterministicAgent(AgentSpec("quant", "Quantitative Underwriting", "medium"), thesis="fallback")
    AgentRunner(provider).run(researcher(), "Assess", EVIDENCE)
    AgentRunner(provider).run(quant, "Assess", EVIDENCE)
    assert real.calls == ["researcher"]


def test_default_provider_remains_deterministic_without_model_key(monkeypatch):
    monkeypatch.delenv("ALETHEIA_MODEL_API_KEY", raising=False)
    provider = build_default_model_provider()
    assert provider.name == "contract"
