from app.model_provider import ResearchContext


def test_research_context_is_structured_and_research_only():
    context = ResearchContext.build(
        "researcher",
        "Fundamental Research",
        "medium",
        "Assess the opportunity",
        [{"evidence_id": "E1", "claim": "Observed fact"}],
    )
    payload = context.as_dict()
    assert payload["agent_id"] == "researcher"
    assert payload["role"] == "Fundamental Research"
    assert payload["evidence"][0]["evidence_id"] == "E1"
    assert "brokerage" not in payload
    assert "credentials" not in payload
    assert "execute" not in payload
