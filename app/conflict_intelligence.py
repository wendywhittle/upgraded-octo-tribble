"""Typed, provenance-aware conflict intelligence.

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


def detect_cre_conflicts(assessments: Iterable[Any]) -> list[dict[str, Any]]:
    """Compare CRE assessments across CRE-specific disagreement dimensions.

    This is an observational projection into the existing conflict engine. It
    never scores or votes for a winning perspective.
    """
    items = list(assessments)
    records: list[dict[str, Any]] = []
    dimensions = (
        ("direction", "recommendation"),
        ("confidence", "confidence"),
        ("time_horizon", "time_horizon"),
        ("evidence", "supporting_evidence"),
        ("contradictory_evidence", "contradictory_evidence"),
        ("assumptions", "assumptions"),
        ("valuation", "assumptions"),
        ("noi_quality", "risks"),
        ("financing", "risks"),
        ("liquidity", "risks"),
        ("leverage", "risks"),
        ("downside", "risks"),
        ("exit_assumptions", "assumptions"),
        ("operational_assumptions", "assumptions"),
        ("invalidation_conditions", "invalidation_conditions"),
    )
    for i, first in enumerate(items):
        for second in items[i + 1:]:
            a = first.__dict__ if hasattr(first, "__dict__") else dict(first)
            b = second.__dict__ if hasattr(second, "__dict__") else dict(second)
            for dimension, key in dimensions:
                left = a.get(key)
                right = b.get(key)
                if left is None or right is None:
                    continue
                left_value = list(left) if not isinstance(left, (str, int, float)) else left
                right_value = list(right) if not isinstance(right, (str, int, float)) else right
                if left_value == right_value:
                    continue
                records.append({
                    "proposition": f"CRE opportunity {a.get('opportunity_id')} has differing {dimension} assessments",
                    "conflict_type": "assumption" if dimension in {"assumptions", "valuation", "financing", "exit_assumptions", "operational_assumptions"} else "uncertainty" if dimension in {"confidence", "invalidation_conditions"} else "interpretive",
                    "perspectives": [a.get("perspective_id"), b.get("perspective_id")],
                    "dimension": dimension,
                    "left": left_value,
                    "right": right_value,
                    "supporting_evidence": _ids(a.get("supporting_evidence", ())) + _ids(b.get("supporting_evidence", ())),
                    "contradicting_evidence": _ids(a.get("contradictory_evidence", ())) + _ids(b.get("contradictory_evidence", ())),
                    "unresolved_questions": [
                        f"Which evidence or assumption explains the {dimension} difference?",
                        "What new evidence would resolve the disagreement?",
                    ],
                    "severity": "material" if dimension in {"downside", "invalidation_conditions", "financing", "leverage"} else "moderate",
                    "status": "unresolved",
                })
    return records
