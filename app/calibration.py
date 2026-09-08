"""Research-only calibration and outcome learning utilities.

Calibration evaluates explicit probabilistic predictions against later outcomes.
Agent confidence is deliberately not interpreted as a probability. Historical
records are treated as immutable inputs; this module produces a new report.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


def calibrate_predictions(records: Iterable[Dict[str, Any]], bins: int = 5) -> Dict[str, Any]:
    """Return calibration metrics for records with explicit probabilities."""
    if bins < 1 or bins > 20:
        raise ValueError("bins must be between 1 and 20")

    usable: List[Dict[str, Any]] = []
    excluded = 0
    for record in records:
        probability = record.get("predicted_probability")
        outcome = record.get("outcome")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            excluded += 1
            continue
        if not 0.0 <= float(probability) <= 1.0 or not isinstance(outcome, bool):
            excluded += 1
            continue
        usable.append({
            "prediction_id": record.get("prediction_id"),
            "agent_id": record.get("agent_id"),
            "probability": float(probability),
            "outcome": int(outcome),
        })

    if not usable:
        return {
            "status": "insufficient_data",
            "sample_count": 0,
            "excluded_count": excluded,
            "brier_score": None,
            "calibration_bins": [],
            "agent_metrics": {},
            "lesson": "No explicit probabilistic predictions have resolved outcomes yet.",
            "historical_records_mutated": False,
            "research_only": True,
            "human_decision_required": True,
            "execution_capability": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
        }

    brier = sum((item["probability"] - item["outcome"]) ** 2 for item in usable) / len(usable)
    calibration_bins = []
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        members = [item for item in usable if (low <= item["probability"] < high) or (index == bins - 1 and item["probability"] == high)]
        if not members:
            continue
        calibration_bins.append({
            "bin": index,
            "lower": round(low, 4),
            "upper": round(high, 4),
            "count": len(members),
            "mean_predicted_probability": round(sum(x["probability"] for x in members) / len(members), 4),
            "observed_frequency": round(sum(x["outcome"] for x in members) / len(members), 4),
        })

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in usable:
        grouped[str(item["agent_id"] or "unknown")].append(item)
    agent_metrics = {
        agent_id: {
            "sample_count": len(items),
            "brier_score": round(sum((x["probability"] - x["outcome"]) ** 2 for x in items) / len(items), 6),
        }
        for agent_id, items in grouped.items()
    }

    return {
        "status": "calculated",
        "sample_count": len(usable),
        "excluded_count": excluded,
        "brier_score": round(brier, 6),
        "calibration_bins": calibration_bins,
        "agent_metrics": agent_metrics,
        "prediction_ids_present": sum(item["prediction_id"] is not None for item in usable),
        "lesson": "Calibration is promising but requires more resolved outcomes." if len(usable) < 30 else "Review bins and agent-level error before trusting probability estimates.",
        "historical_records_mutated": False,
        "research_only": True,
        "human_decision_required": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
