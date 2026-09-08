from app.agent_registry import build_default_registry, run_default_agents


def test_default_roster_contains_expected_perspectives():
    registry = build_default_registry()
    assert registry.ids() == [
        "researcher", "quant", "investor", "scientist", "systems",
        "contrarian", "philosopher", "observer", "meta_intelligence", "governance",
    ]


def test_default_roster_is_research_only():
    results = run_default_agents("Test question")
    assert len(results) == 10
    assert all(item["human_decision_required"] for item in results)
    assert all(not item["capability_profile"]["execute"] for item in results)
    assert all(not item["capability_profile"]["brokerage"] for item in results)
    assert all(not item["capability_profile"]["portfolio_mutation"] for item in results)


def test_default_agents_without_verified_evidence_return_no_data():
    results = run_default_agents("Test question")
    assert all(item["direction"] == "NO_DATA" for item in results)
    assert all(item["confidence"] == 0.0 for item in results)
