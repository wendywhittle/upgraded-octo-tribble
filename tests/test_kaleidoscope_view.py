from app.kaleidoscope_view import build_kaleidoscope_view


def test_view_preserves_perspectives_and_authority_boundary():
    agents = [
        {"agent_id": "researcher", "role": "Fundamental Research", "direction": "LONG", "confidence": 0.7, "horizon": "medium", "evidence": [{"evidence_id": "E1"}], "model_version": "test"},
        {"agent_id": "contrarian", "role": "Adversarial Challenge", "direction": "SHORT", "confidence": 0.8, "horizon": "short", "evidence": [{"evidence_id": "E1"}], "model_version": "test"},
    ]
    view = build_kaleidoscope_view(agents, conflicts=[{"type": "same_horizon_conflict"}])
    assert view["perspective_count"] == 2
    assert view["perspectives"][0]["direction"] == "LONG"
    assert view["conflicts"][0]["type"] == "same_horizon_conflict"
    assert view["read_only"] is True
    assert view["execution_capability"] is False
    assert view["brokerage_connectivity"] is False
    assert view["portfolio_mutation"] is False
    assert view["human_decision_required"] is True
