from pathlib import Path

from app.memory import append_record, build_record, read_records
from app.observer import observe


def test_memory_is_append_only_and_reconstructable(tmp_path: Path):
    path = tmp_path / "memory.jsonl"
    record = build_record("test", [], {"conflicts": [], "horizon_divergences": []},
                          {"independent_of_agents": True}, {"recommendation": "hold"},
                          {"verdict": "HOLD"}, {"human_decision_required": True}, 42)
    append_record(record, path)
    records = read_records(path)
    assert len(records) == 1
    assert records[0]["question"] == "test"
    assert records[0]["audit"]["reconstructable"] is True
    assert records[0]["outcome"]["status"] == "pending"


def test_observer_does_not_convert_pending_outcome_into_learning():
    result = observe("test", [{"agent_id": "a", "direction": "LONG", "confidence": .7}],
                     {"conflicts": [], "horizon_divergences": []},
                     {"independent_of_agents": True}, {"recommendation": "hold"},
                     {"verdict": "HOLD"})
    assert result["status"] == "observed"
    assert result["outcome_status"] == "pending"
    assert result["learning_status"] == "awaiting_outcome"
