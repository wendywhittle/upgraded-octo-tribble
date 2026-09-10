from datetime import datetime, timezone

import pytest

from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner
from app.analysis_pipeline import run_analysis
from app.model_inference import CallableModelProvider

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def evidence():
    return [{
        "evidence_id": "E-MODEL-1",
        "source": "unit-test-source",
        "claim": "Test evidence supports a research assessment.",
        "observed_at": "2026-09-08T11:00:00+00:00",
        "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary"},
        "point_in_time": True,
    }]


def model_output(context):
    return {
        "agent_id": context["agent"]["agent_id"],
        "direction": "NEUTRAL",
        "confidence": 0.5,
        "thesis": f"Injected model assessed {context['agent']['role']}.",
        "evidence": context["evidence"],
        "horizon": context["agent"]["default_horizon"],
        "strategy": context["agent"]["role"],
        "model_version": "test-model-1",
        "assumptions": ["Test assumption"],
        "invalidation_conditions": ["Test invalidation"],
    }


def test_callable_provider_receives_structured_context_and_runner_validates():
    seen = []

    def invoke(context):
        seen.append(context)
        return model_output(context)

    agent = DeterministicAgent(
        AgentSpec("test", "Test Perspective", "medium"),
        "NEUTRAL", 0.5, "fallback thesis", "fallback challenge",
    )
    result = AgentRunner(CallableModelProvider(invoke)).run(agent, "Test question", evidence())

    assert len(seen) == 1
    assert seen[0]["agent"]["agent_id"] == "test"
    assert seen[0]["instructions"]["execution_allowed"] is False
    assert result["provider"] == "injected-model"
    assert result["model_version"] == "test-model-1"
    assert result["human_decision_required"] is True
    assert result["execution_capability"] is False


def test_malformed_model_output_is_rejected():
    provider = CallableModelProvider(lambda context: {"agent_id": context["agent"]["agent_id"]})
    agent = DeterministicAgent(
        AgentSpec("test", "Test Perspective", "medium"),
        "NEUTRAL", 0.5, "fallback thesis", "fallback challenge",
    )
    with pytest.raises(ValueError, match="invalid AgentOutput"):
        AgentRunner(provider).run(agent, "Test question", evidence())


def test_provider_cannot_escalate_agent_capabilities():
    def malicious(context):
        result = model_output(context)
        result["capability_profile"] = {"execute": True, "brokerage": True, "portfolio_mutation": True}
        return result

    agent = DeterministicAgent(
        AgentSpec("test", "Test Perspective", "medium"),
        "NEUTRAL", 0.5, "fallback thesis", "fallback challenge",
    )
    result = AgentRunner(CallableModelProvider(malicious)).run(agent, "Test question", evidence())
    assert result["capability_profile"]["execute"] is False
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False


def test_full_pipeline_uses_injected_provider_for_active_perspectives(monkeypatch):
    calls = []

    def invoke(context):
        calls.append(context["agent"]["agent_id"])
        return model_output(context)

    monkeypatch.setattr("app.analysis_pipeline.append_record", lambda record: None)
    result = run_analysis("Assess the test opportunity", evidence(), now=NOW, paths=100, provider=CallableModelProvider(invoke))

    assert len(calls) == 6
    assert set(calls) == {"researcher", "quant", "investor", "systems", "skeptic", "contrarian"}
    assert result["audit"]["provider"] == "injected-model"
    assert result["audit"]["research_only"] is True
    assert result["governance"]["human_decision_required"] is True
    assert result["governance"]["autonomous_execution"] is False


def test_default_pipeline_remains_contract_provider(monkeypatch):
    monkeypatch.setattr("app.analysis_pipeline.append_record", lambda record: None)
    result = run_analysis("Assess the test opportunity", evidence(), now=NOW, paths=100)
    assert result["audit"]["provider"] == "contract"
    assert result["agents"]
    assert all(agent["provider"] == "contract" for agent in result["agents"])
