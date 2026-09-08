from app.agent_contract import AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner, CallableModelProvider


def test_callable_model_provider_receives_only_research_context():
    captured = {}

    def model(payload):
        captured.update(payload)
        return {
            "agent_id": payload["agent_id"],
            "thesis": "Model-backed research assessment",
            "direction": "NEUTRAL",
            "confidence": 0.5,
            "horizon": payload["horizon"],
        }

    agent = DeterministicAgent(spec=AgentSpec("quant", "Quantitative Underwriting", "medium"))
    provider = CallableModelProvider(model, name="test-model")
    result = AgentRunner(provider).run(
        agent,
        "Assess the research question",
        [{"evidence_id": "E1", "source": "test", "claim": "Observed fact"}],
    )

    assert captured["agent_id"] == "quant"
    assert captured["role"] == "Quantitative Underwriting"
    assert captured["question"] == "Assess the research question"
    assert captured["evidence"][0]["evidence_id"] == "E1"
    assert "brokerage" not in captured
    assert "credentials" not in captured
    assert "execute" not in captured
    assert result["provider"] == "test-model"
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False


def test_callable_model_provider_rejects_non_dict_output():
    agent = DeterministicAgent(spec=AgentSpec("quant", "Quantitative Underwriting", "medium"))
    provider = CallableModelProvider(lambda payload: "not structured")

    try:
        AgentRunner(provider).run(agent, "Question", [])
    except TypeError as exc:
        assert "dictionary" in str(exc)
    else:
        raise AssertionError("Expected TypeError")
