"""Small in-memory adapter from learning artifacts to Epistemic Memory records.

This module does not persist records and does not perform calculations. Existing
learning/calibration code remains authoritative for derived results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List

from app.epistemic_memory import EpistemicRecord, EpistemicRecordType


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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record(
    record_id: str,
    record_type: EpistemicRecordType,
    content: Dict[str, Any],
    *,
    created_at: datetime | None = None,
    effective_at: datetime | None = None,
    observed_at: datetime | None = None,
    source_refs: List[str] | None = None,
    related_record_ids: List[str] | None = None,
    provenance: Dict[str, Any] | None = None,
) -> EpistemicRecord:
    return EpistemicRecord(
        record_id=record_id,
        record_type=record_type,
        created_at=created_at or _now(),
        effective_at=effective_at,
        observed_at=observed_at,
        source_refs=source_refs or [],
        provenance=provenance or {"adapter": "app.epistemic_adapter"},
        related_record_ids=related_record_ids or [],
        content=content,
    )


def prediction_to_epistemic_records(prediction: Dict[str, Any]) -> List[EpistemicRecord]:
    """Represent an issued forecast and its explicit assumptions without mutation."""
    prediction_id = prediction.get("prediction_id")
    if not isinstance(prediction_id, str) or not prediction_id.strip():
        return []

    created_at = _parse_timestamp(prediction.get("predicted_at") or prediction.get("recorded_at")) or _now()
    hypothesis_id = f"hypothesis:{prediction_id}"
    records = [
        _record(
            hypothesis_id,
            "hypothesis",
            {
                "prediction_id": prediction_id,
                "question": prediction.get("question"),
                "predicted_probability": prediction.get("predicted_probability"),
                "agent_id": prediction.get("agent_id"),
                "model_version": prediction.get("model_version"),
                "horizon": prediction.get("horizon"),
            },
            created_at=created_at,
            effective_at=created_at,
            source_refs=[str(item.get("evidence_id")) for item in prediction.get("evidence", []) if isinstance(item, dict) and item.get("evidence_id")],
        )
    ]

    for index, assumption in enumerate(prediction.get("assumptions") or []):
        if not isinstance(assumption, (str, int, float, bool)):
            continue
        records.append(
            _record(
                f"assumption:{prediction_id}:{index}",
                "assumption",
                {"prediction_id": prediction_id, "statement": str(assumption)},
                created_at=created_at,
                effective_at=created_at,
                related_record_ids=[hypothesis_id],
            )
        )
    return records


def resolution_to_epistemic_records(resolution: Dict[str, Any]) -> List[EpistemicRecord]:
    """Represent an observed outcome and its existing Brier attribution separately."""
    prediction_id = resolution.get("prediction_id")
    if not isinstance(prediction_id, str) or not prediction_id.strip():
        return []

    observed_at = _parse_timestamp(resolution.get("resolved_at")) or _now()
    hypothesis_id = f"hypothesis:{prediction_id}"
    outcome_id = f"outcome:{prediction_id}"
    attribution_id = f"attribution:{prediction_id}"
    outcome_source = resolution.get("outcome_source")
    source_refs = [str(outcome_source)] if outcome_source else []

    outcome = _record(
        outcome_id,
        "outcome",
        {
            "prediction_id": prediction_id,
            "outcome": resolution.get("outcome"),
            "resolved_at": resolution.get("resolved_at"),
            "outcome_source": outcome_source,
        },
        created_at=observed_at,
        effective_at=observed_at,
        observed_at=observed_at,
        source_refs=source_refs,
        related_record_ids=[hypothesis_id],
    )
    attribution = _record(
        attribution_id,
        "attribution",
        {
            "prediction_id": prediction_id,
            "predicted_probability": resolution.get("predicted_probability"),
            "brier_error": resolution.get("brier_error"),
            "assessment": "Brier error for the resolved forecast; no historical forecast mutation.",
        },
        created_at=observed_at,
        observed_at=observed_at,
        related_record_ids=[hypothesis_id, outcome_id],
    )
    return [outcome, attribution]


def observer_to_epistemic_record(observer: Dict[str, Any]) -> EpistemicRecord:
    """Represent the Observer's current observation as an interpretation record."""
    question = str(observer.get("question") or "")
    fingerprint = sha256(
        f"{question}|{observer.get('synthesis_verdict')}|{observer.get('agent_count')}|{observer.get('outcome_status')}".encode("utf-8")
    ).hexdigest()[:16]
    return _record(
        f"interpretation:observer:{fingerprint}",
        "interpretation",
        dict(observer),
        observed_at=_now(),
        provenance={"adapter": "app.epistemic_adapter", "source": "observer"},
    )


def learning_to_epistemic_records(learning_report: Dict[str, Any]) -> List[EpistemicRecord]:
    """Represent only the lessons the existing learning engine already derives."""
    records: List[EpistemicRecord] = []
    for lesson in learning_report.get("lessons", []):
        if not isinstance(lesson, dict):
            continue
        agent_id = str(lesson.get("agent_id") or "unknown")
        lesson_type = str(lesson.get("type") or "observation")
        sample_count = lesson.get("sample_count")
        record_id = f"lesson:{agent_id}:{lesson_type}:{sample_count}"
        records.append(
            _record(
                record_id,
                "lesson",
                dict(lesson),
                related_record_ids=[],
                provenance={"adapter": "app.epistemic_adapter", "source": "learning_report"},
            )
        )
    return records
