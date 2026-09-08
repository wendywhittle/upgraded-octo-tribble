"""Point-in-time dataset construction for AletheiaTelos Experiment #001.

The adapter intentionally accepts normalized historical observations rather than
scraping a vendor endpoint. This keeps the experiment reproducible, provenance-
aware, and independent of a particular data vendor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from .experiment_001 import Observation


@dataclass(frozen=True)
class HistoricalPoint:
    """One synchronized daily observation with explicit provenance."""

    observed_at: str
    spx_close: float
    vix_level: float
    skew_level: float
    available_at: str
    source_id: str
    content_hash: str


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp timezone is required.")
    return parsed.astimezone(timezone.utc)


def validate_points(points: Sequence[HistoricalPoint]) -> List[HistoricalPoint]:
    """Validate ordering, provenance, timestamps, and numeric market values."""
    if not points:
        raise ValueError("Historical dataset cannot be empty.")

    parsed_points = [(_parse_timestamp(point.observed_at), point) for point in points]
    ordered_pairs = sorted(parsed_points, key=lambda item: item[0])
    seen = set()
    for observed, point in ordered_pairs:
        if observed in seen:
            raise ValueError(f"Duplicate observation timestamp: {point.observed_at}")
        seen.add(observed)
        available = _parse_timestamp(point.available_at)
        if available > observed:
            raise ValueError(
                "Point-in-time violation: data became available after its observation timestamp."
            )
        if point.spx_close <= 0 or point.vix_level <= 0 or point.skew_level <= 0:
            raise ValueError("SPX, VIX, and SKEW levels must be positive.")
        if not point.source_id.strip() or not point.content_hash.strip():
            raise ValueError("Every historical point requires source_id and content_hash.")
    return [point for _, point in ordered_pairs]


def build_experiment_observations(
    points: Sequence[HistoricalPoint],
    horizon_days: int = 5,
) -> List[Observation]:
    """Construct Experiment #001 features and future labels without look-ahead.

    The label is the worst SPX close-to-close return from the observation close
    across the following ``horizon_days`` trading sessions. Future prices are
    used only for the label and never for any feature.
    """
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive.")
    ordered = validate_points(points)
    if len(ordered) < horizon_days + 6:
        raise ValueError("Not enough observations to construct 5-day features and labels.")

    observations: List[Observation] = []
    for i in range(5, len(ordered) - horizon_days):
        current = ordered[i]
        prior = ordered[i - 5]
        future = ordered[i + 1 : i + horizon_days + 1]
        current_spx = current.spx_close

        future_max_drawdown = min(point.spx_close / current_spx - 1.0 for point in future)
        observations.append(
            Observation(
                observed_at=current.observed_at,
                spx_return_5d=current_spx / prior.spx_close - 1.0,
                vix_level=current.vix_level,
                vix_change_5d=current.vix_level / prior.vix_level - 1.0,
                skew_level=current.skew_level,
                skew_change_5d=current.skew_level / prior.skew_level - 1.0,
                future_max_drawdown=future_max_drawdown,
            )
        )
    return observations


def build_observations_from_rows(rows: Iterable[dict], horizon_days: int = 5) -> List[Observation]:
    """Parse normalized row dictionaries for CSV/API adapters.

    Required keys are deliberately explicit so a vendor-specific adapter must
    make its timestamp and provenance mapping visible at the boundary.
    """
    points = [
        HistoricalPoint(
            observed_at=str(row["observed_at"]),
            spx_close=float(row["spx_close"]),
            vix_level=float(row["vix_level"]),
            skew_level=float(row["skew_level"]),
            available_at=str(row["available_at"]),
            source_id=str(row["source_id"]),
            content_hash=str(row["content_hash"]),
        )
        for row in rows
    ]
    return build_experiment_observations(points, horizon_days=horizon_days)
