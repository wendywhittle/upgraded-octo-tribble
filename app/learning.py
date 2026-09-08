"""Research-only institutional learning projection.

This module derives lessons from immutable prediction-resolution records. It never
changes agent authority, weights, execution capability, or historical records.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from app.calibration import calibrate_predictions


def build_learning_report(records: Iterable[Dict[str, Any]], bins: int = 5) -> Dict[str, Any]:
    """Build calibration and learning metadata from resolved prediction records."""
    resolutions: List[Dict[str, Any]] = [
        dict(record)
        for record in records
        if record.get("record_type") == "prediction_resolution"
    ]
    calibration = calibrate_predictions(resolutions, bins=bins)
    agent_metrics = calibration.get("agent_metrics", {})
    ranked = sorted(
        (
            {"agent_id": agent_id, **metrics}
            for agent_id, metrics in agent_metrics.items()
        ),
        key=lambda item: (item["brier_score"], -item["sample_count"]),
    )
    return {
        "record_type": "learning_report",
        "status": calibration.get("status"),
        "resolved_prediction_count": len(resolutions),
        "calibration": calibration,
        "agent_metrics": agent_metrics,
        "agent_metrics_ranked": ranked,
        "authority_changed": False,
        "weights_changed": False,
        "historical_records_mutated": False,
        "learning_mode": "informational_only",
        "research_only": True,
        "human_decision_required": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
