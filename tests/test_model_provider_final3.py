from app.model_provider import ResearchContext


def test_context_is_research_only():
    context = ResearchContext.build("quant", "Quantitative Underwriting", "medium", "Q", [])
    payload = context.as_dict()
    assert set(payload) == {"agent_id", "role", "horizon", "question", "evidence"}
