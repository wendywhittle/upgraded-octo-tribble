"""Research-only resolution of explicit probabilistic forecasts.

A forecast is immutable once issued. Resolution creates a separate record that
attaches the later observed outcome to the forecast and computes its Brier error.
This module does not change agent authority, weights, or trading behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def resolve_prediction(
    prediction: Dict[str, Any],
    outcome: bool,
    resolved_at: str,
    outcome_source: str | None = None,
) -> Dict[str, Any]:
    """Resolve one explicit probability forecast without mutating its source record."""
    prediction_id = prediction.get("prediction_id")
    probability = prediction.get("predicted_probability")
    if not isinstance(prediction_id, str) or not prediction_id.strip():
        raise ValueError("prediction_id is required")
    if not isinstance(probability, (int, float)) or isinstance(probability, bool):
        raise ValueError("predicted_probability must be an explicit number")
    probability = float(probability)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("predicted_probability must be between 0 and 1")
    if not isinstance(outcome, bool):
        raise ValueError("outcome must be boolean")
    resolved_dt = _parse_timestamp(resolved_at)
    if resolved_dt is None:
        raise ValueError("resolved_at must be a valid timestamp")
    issued_at = _parse_timestamp(prediction.get("predicted_at") or prediction.get("recorded_at"))
    if issued_at is not None and resolved_dt < issued_at:
        raise ValueError("resolved_at cannot precede forecast issuance")

    result = {
        "record_type": "prediction_resolution",
        "prediction_id": prediction_id,
        "agent_id": prediction.get("agent_id"),
        "model_version": prediction.get("model_version"),
        "question": prediction.get("question"),
        "horizon": prediction.get("horizon"),
        "predicted_probability": probability,
        "outcome": outcome,
        "brier_error": round((probability - int(outcome)) ** 2, 6),
        "resolved_at": resolved_dt.isoformat(),
        "outcome_source": outcome_source,
        "historical_prediction_mutated": False,
        "research_only": True,
        "human_decision_required": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
    return result
