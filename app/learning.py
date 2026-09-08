"""Research-only institutional learning projection.

This module derives lessons from immutable prediction-resolution records. It never
changes agent authority, weights, execution capability, or historical records.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from app.calibration import calibrate_predictions


def _group_metrics(records: List[Dict[str, Any]], key_name: str) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = str(record.get(key_name) or "unknown")
        grouped[key].append(record)
    result: Dict[str, Any] = {}
    for key, items in grouped.items():
        result[key] = {
            "sample_count": len(items),
            "brier_score": round(
                sum(float(item["brier_error"]) for item in items) / len(items), 6
            ),
        }
    return result


def _lessons(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lessons: List[Dict[str, Any]] = []
    by_agent: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_agent[str(record.get("agent_id") or "unknown")].append(record)

    for agent_id, items in by_agent.items():
        if len(items) < 3:
            continue
        mean_probability = sum(float(x["predicted_probability"]) for x in items) / len(items)
        mean_outcome = sum(int(bool(x["outcome"])) for x in items) / len(items)
        gap = mean_probability - mean_outcome
        if gap >= 0.15:
            lessons.append({"type": "overconfidence", "agent_id": agent_id, "sample_count": len(items), "gap": round(gap, 4)})
        elif gap <= -0.15:
            lessons.append({"type": "underconfidence", "agent_id": agent_id, "sample_count": len(items), "gap": round(gap, 4)})

    return lessons


def build_learning_report(records: Iterable[Dict[str, Any]], bins: int = 5) -> Dict[str, Any]:
    """Build calibration and learning metadata from resolved prediction records."""
    resolutions: List[Dict[str, Any]] = [
        dict(record)
        for record in records
        if record.get("record_type") == "prediction_resolution"
        and isinstance(record.get("predicted_probability"), (int, float))
        and not isinstance(record.get("predicted_probability"), bool)
        and isinstance(record.get("outcome"), bool)
    ]
    calibration = calibrate_predictions(resolutions, bins=bins)
    agent_metrics = calibration.get("agent_metrics", {})
    ranked = sorted(
        ({"agent_id": agent_id, **metrics} for agent_id, metrics in agent_metrics.items()),
        key=lambda item: (item["brier_score"], -item["sample_count"]),
    )
    horizon_metrics = _group_metrics(resolutions, "horizon") if resolutions and all("brier_error" in r for r in resolutions) else {}
    return {
        "record_type": "learning_report",
        "status": calibration.get("status"),
        "resolved_prediction_count": len(resolutions),
        "calibration": calibration,
        "agent_metrics": agent_metrics,
        "agent_metrics_ranked": ranked,
        "horizon_metrics": horizon_metrics,
        "lessons": _lessons(resolutions),
        "authority_changed": False,
        "weights_changed": False,
        "historical_records_mutated": False,
        "learning_mode": "informational_only",
        "adaptation_policy": "No automatic authority, weight, permission, or execution changes are permitted.",
        "research_only": True,
        "human_decision_required": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
