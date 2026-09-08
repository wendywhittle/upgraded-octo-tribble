from app.agent_registry import build_default_registry
from app.model_backend import CallableModelBackend


def test_backend_context_contains_only_research_capabilities():
    seen = {}

    def invoke(context):
        seen.update(context)
        return {"direction": "NO_DATA", "confidence": 0.0, "thesis": "insufficient evidence"}

    agent = build_default_registry().get("governance")
    CallableModelBackend(invoke).assess(agent, "q", [])

    assert set(seen["constraints"]) == {
        "research_only",
        "execution_capability",
        "brokerage_connectivity",
        "portfolio_mutation",
        "human_decision_required",
    }
    assert seen["constraints"]["research_only"] is True
    assert seen["constraints"]["execution_capability"] is False
    assert seen["constraints"]["brokerage_connectivity"] is False
    assert seen["constraints"]["portfolio_mutation"] is False
    assert seen["constraints"]["human_decision_required"] is True
