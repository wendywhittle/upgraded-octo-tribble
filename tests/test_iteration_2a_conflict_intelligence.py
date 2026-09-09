from app.conflict_intelligence import detect_conflict_intelligence
from app.schemas import ConflictRecord


def _agent(agent_id, direction, evidence_basis, assumptions=None, horizon="medium"):
    return {
        "agent_id": agent_id,
        "question": "Assess the opportunity",
        "direction": direction,
        "confidence": 0.6,
        "horizon": horizon,
        "evidence_basis": evidence_basis,
        "contradictory_evidence_basis": [],
        "assumptions": assumptions or ["Assessment is dependent on supplied evidence."],
    }


def test_conflict_intelligence_is_typed_and_keeps_perspectives_visible():
    records = detect_conflict_intelligence([
        _agent("researcher", "LONG", ["E-1"]),
        _agent("contrarian", "SHORT", ["E-1"]),
    ])
    assert len(records) == 1
    record = ConflictRecord(**records[0])
    assert record.conflict_type == "interpretive"
    assert record.perspectives == ["researcher", "contrarian"]
    assert record.status == "unresolved"
    assert "E-1" in record.supporting_evidence


def test_conflict_intelligence_distinguishes_evidence_and_assumption_conflicts():
    evidence_conflict = detect_conflict_intelligence([
        _agent("a", "LONG", ["E-1"]),
        _agent("b", "SHORT", ["E-2"]),
    ])[0]
    assert evidence_conflict["conflict_type"] == "evidentiary"

    assumption_conflict = detect_conflict_intelligence([
        _agent("a", "LONG", ["E-1"], ["Assumption A"]),
        _agent("b", "SHORT", ["E-1"], ["Assumption B"]),
    ])[0]
    assert assumption_conflict["conflict_type"] == "assumption"


def test_horizon_difference_is_not_treated_as_same_horizon_conflict():
    records = detect_conflict_intelligence([
        _agent("a", "LONG", ["E-1"], horizon="short"),
        _agent("b", "SHORT", ["E-1"], horizon="long"),
    ])
    assert records[0]["conflict_type"] == "horizon"


def test_no_data_does_not_create_conflict():
    records = detect_conflict_intelligence([
        _agent("researcher", "NO_DATA", []),
        _agent("contrarian", "SHORT", ["E-1"]),
    ])
    assert records == []


def test_perspectives_do_not_receive_other_conclusions():
    from app.evidence_orchestration import distribute_evidence

    evidence = [{"evidence_id": "E-1", "source": "source", "claim": "Observed fact."}]
    distributed = distribute_evidence(evidence, ["researcher", "quant", "skeptic", "contrarian"])
    assert all(items == evidence for items in distributed.values())
    assert all("direction" not in items[0] for items in distributed.values())
