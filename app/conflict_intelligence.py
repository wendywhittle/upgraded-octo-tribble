"""Typed, provenance-aware conflict intelligence for AletheiaTelos.

This layer makes disagreement legible without averaging perspectives or selecting
an authoritative winner. It compares structured outputs only; it never executes,
mutates portfolios, or determines simulation outcomes.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from app.schemas import ConflictRecord


def _ids(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if value is not None]


def _classify(first: Dict[str, Any], second: Dict[str, Any]) -> str:
    if first.get("horizon") != second.get("horizon"):
        return "horizon"
    first_evidence = set(_ids(first.get("evidence_basis", [])))
    second_evidence = set(_ids(second.get("evidence_basis", [])))
    if first_evidence and second_evidence and not first_evidence.intersection(second_evidence):
        return "evidentiary"
    first_assumptions = set(first.get("assumptions", []))
    second_assumptions = set(second.get("assumptions", []))
    if first_assumptions != second_assumptions:
        return "assumption"
    return "interpretive"


def detect_conflict_intelligence(agents: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Return typed conflict records for substantive perspective disagreement."""
    agent_list = [dict(agent) for agent in agents]
    records: list[Dict[str, Any]] = []
    for index, first in enumerate(agent_list):
        for second in agent_list[index + 1 :]:
            direction_a = first.get("direction")
            direction_b = second.get("direction")
            if direction_a in {"NEUTRAL", "NO_DATA"} or direction_b in {"NEUTRAL", "NO_DATA"}:
                continue
            if direction_a == direction_b and first.get("assumptions", []) == second.get("assumptions", []):
                continue

            contradictory = _ids(first.get("contradictory_evidence_basis", [])) + _ids(second.get("contradictory_evidence_basis", []))
            supporting = _ids(first.get("evidence_basis", [])) + _ids(second.get("evidence_basis", []))
            conflict_type = _classify(first, second)
            if direction_a != direction_b and conflict_type == "horizon":
                conflict_type = "horizon"
            elif direction_a != direction_b and conflict_type not in {"evidentiary", "assumption"}:
                conflict_type = "interpretive"

            record = {
                "proposition": f"Assessment of: {first.get('question', '')}",
                "conflict_type": conflict_type,
                "perspectives": [first.get("agent_id"), second.get("agent_id")],
                "supporting_evidence": supporting,
                "contradicting_evidence": contradictory,
                "assumption_conflicts": [
                    {"perspective": first.get("agent_id"), "assumptions": list(first.get("assumptions", []))},
                    {"perspective": second.get("agent_id"), "assumptions": list(second.get("assumptions", []))},
                ],
                "unresolved_questions": [
                    "Which evidence or assumption explains the disagreement?",
                    "What new evidence would resolve the disagreement?",
                ],
                "severity": "material" if direction_a != direction_b else "moderate",
                "status": "unresolved",
            }
            validated = ConflictRecord(**record)
            records.append(validated.model_dump() if hasattr(validated, "model_dump") else validated.dict())
    return records
