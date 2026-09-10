from app.meta_intelligence import evaluate


def agent(agent_id, direction, evidence_id="E-1", assumptions=None, confidence=0.8):
    return {
        "agent_id": agent_id,
        "direction": direction,
        "confidence": confidence,
        "evidence": [{"evidence_id": evidence_id}],
        "assumptions": assumptions or [],
        "invalidation_conditions": ["Core assumption fails"],
    }


def test_meta_intelligence_detects_shared_reasoning_without_directional_vote():
    result = evaluate(
        [
            agent("quant", "LONG", assumptions=["Stable financing"]),
            agent("investor", "LONG", assumptions=["Stable financing"]),
            agent("systems", "SHORT"),
        ],
        evidence={"count": 1, "usable_count": 1},
    )
    assert result["directional_vote"] is None
    assert result["false_consensus_risk"] in {"MEDIUM", "HIGH"}
    assert result["correlated_reasoning_risk"] in {"MEDIUM", "HIGH"}
    assert result["assumption_concentration"]


def test_meta_intelligence_surfaces_unresolved_conflict_and_uncertainty():
    result = evaluate(
        [agent("quant", "LONG", confidence=0.9), agent("systems", "SHORT", confidence=0.85)],
        evidence={"count": 1, "usable_count": 1},
        conflicts=[{
            "conflict_record": {
                "status": "unresolved",
                "unresolved_questions": ["Which financing assumption is correct?"],
            }
        }],
        simulation={"independent_of_agents": True},
        skeptic={"challenges": ["Downside remains material."]},
    )
    assert "Which financing assumption is correct?" in result["unresolved_conflicts"]
    assert result["uncertainty_concern"]
    assert result["recommended_next_step"] == "INVESTIGATE_CONFLICT"


def test_meta_intelligence_preserves_execution_boundary():
    result = evaluate([agent("investor", "LONG")])
    assert result["human_review_required"] is True
    assert result["execution_capability"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False


def test_meta_intelligence_identifies_missing_evidence_and_invalidation_conditions():
    weak = agent("investor", "LONG")
    weak["evidence"] = []
    weak["invalidation_conditions"] = []
    result = evaluate([weak], evidence={"count": 1, "usable_count": 0})
    assert result["evidence_quality_concern"]
    assert result["regime_or_invalidation_concern"]
    assert result["recommended_next_step"] == "GATHER_MORE_EVIDENCE"
