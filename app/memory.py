"""Append-only epistemic memory for reconstructable decisions."""

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Dict, List

MEMORY_PATH = Path("data/epistemic_memory.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_record(question: str, agents: List[Dict[str, Any]], conflicts: Dict[str, Any],
                 simulation: Dict[str, Any], skeptic: Dict[str, Any],
                 synthesis: Dict[str, Any], governance: Dict[str, Any], seed: int) -> Dict[str, Any]:
    return {
        "record_type": "decision_observation",
        "recorded_at": _now(),
        "question": question,
        "agents": agents,
        "conflicts": conflicts,
        "simulation": simulation,
        "skeptic": skeptic,
        "synthesis": synthesis,
        "governance": governance,
        "outcome": {"status": "pending", "value": None, "observed_at": None},
        "lesson": None,
        "audit": {"simulation_seed": seed, "reconstructable": True},
    }


def append_record(record: Dict[str, Any], path: Path = MEMORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_records(path: Path = MEMORY_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records
