from datetime import datetime, timezone

from app.evidence_orchestration import distribute_evidence, run_evidence_fed_agents


NOW = datetime(2026, 9, 8, 17, 0, tzinfo=timezone.utc)


def evidence_item(evidence_id="e1", decision_usable=True):
    return {
        "evidence_id": evidence_id,
        "source": "research-source",
        "claim": "Observed market condition is material.",
        "observed_at": NOW.isoformat(),
        "retrieved_at": NOW.isoformat(),
        "decision_usable": decision_usable,
        "provenance": {"type": "primary", "point_in_time": True},
    }


def test_distribute_evidence_is_explicit_and_uniform():
    item = evidence_item()
    result = distribute_evidence([item], ["researcher", "quant"])
    assert result["researcher"] == [item]
    assert result["quant"] == [item]


def test_evidence_fed_runner_uses_only_validated_evidence():
    result = run_evidence_fed_agents(
        "Assess the opportunity.",
        [evidence_item(), evidence_item("blocked", decision_usable=False)],
        now=NOW,
    )
    assert result["agent_count"] == 6
    assert result["active_perspectives"] == ["researcher", "quant", "investor", "systems", "skeptic", "contrarian"]
    assert result["registered_agent_count"] == 10
    assert result["evidence_count"] == 2
    assert result["usable_evidence_count"] == 1
    assert result["blocked_evidence_count"] == 1
    assert all(agent["direction"] != "NO_DATA" for agent in result["agents"])
    assert all(agent["evidence_basis"] == ["e1"] for agent in result["agents"])
    assert result["perspectives_share_conclusions"] is False
    assert result["research_only"] is True
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False
    assert result["human_decision_required"] is True


def test_evidence_fed_runner_returns_no_data_without_usable_evidence():
    result = run_evidence_fed_agents(
        "Assess the opportunity.",
        [evidence_item(decision_usable=False)],
        now=NOW,
    )
    assert all(agent["direction"] == "NO_DATA" for agent in result["agents"])
    assert all(agent["confidence"] == 0.0 for agent in result["agents"])


def test_evidence_fed_runner_rejects_empty_question():
    try:
        run_evidence_fed_agents("   ", [], now=NOW)
    except ValueError as exc:
        assert "Question" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
