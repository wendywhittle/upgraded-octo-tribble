"""Research-only calibration and outcome learning utilities.

Calibration evaluates explicit probabilistic predictions against later outcomes.
Agent confidence is deliberately not interpreted as a probability. Historical
records are treated as immutable inputs; this module produces a new report.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


def calibrate_predictions(records: Iterable[Dict[str, Any]], bins: int = 5) -> Dict[str, Any]:
    """Return calibration metrics for records containing explicit probabilities.

    Each usable record must contain ``predicted_probability`` in [0, 1] and a
    boolean ``outcome``. Records without both fields are reported as excluded.
    """
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
        usable.append({"probability": float(probability), "outcome": int(outcome)})

    if not usable:
        return {
            "status": "insufficient_data",
            "sample_count": 0,
            "excluded_count": excluded,
            "brier_score": None,
            "calibration_bins": [],
            "lesson": "No explicit probabilistic predictions have resolved outcomes yet.",
            "research_only": True,
        }

    brier = sum((item["probability"] - item["outcome"]) ** 2 for item in usable) / len(usable)
    calibration_bins = []
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        members = [
            item for item in usable
            if (low <= item["probability"] < high) or (index == bins - 1 and item["probability"] == high)
        ]
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

    lesson = "Calibration is promising but requires more resolved outcomes." if len(usable) < 30 else (
        "Review bins with the largest prediction-frequency gap before trusting the probability estimates."
    )
    return {
        "status": "calculated",
        "sample_count": len(usable),
        "excluded_count": excluded,
        "brier_score": round(brier, 6),
        "calibration_bins": calibration_bins,
        "lesson": lesson,
        "historical_records_mutated": False,
        "research_only": True,
        "human_decision_required": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
