"""Authorized-data runner for AletheiaTelos Experiment #001."""

from __future__ import annotations

from typing import Dict

from .experiment_001 import Experiment001Spec, evaluate_experiment_001
from .experiment_001_csv import HistoricalRow, dataset_content_hash, parse_csv
from .experiment_001_data import HistoricalPoint, build_experiment_observations
from .experiment_001_manifest import build_dataset_manifest

SCHEMA_VERSION = "EXP-001-CANONICAL-CSV-v1"


def _points(rows: tuple[HistoricalRow, ...]) -> list[HistoricalPoint]:
    return [
        HistoricalPoint(
            observed_at=row.observed_at,
            spx_close=row.spx_close,
            vix_level=row.vix_close,
            skew_level=row.skew_close,
            available_at=row.available_at,
            source_id=row.source_id,
            content_hash=row.content_hash,
        )
        for row in rows
    ]


def run_experiment_001_from_csv(
    csv_text: str,
    spec: Experiment001Spec = Experiment001Spec(),
) -> Dict[str, object]:
    """Validate, fingerprint, manifest, and evaluate an authorized dataset."""
    rows = parse_csv(csv_text)
    if not rows:
        raise ValueError("Experiment #001 dataset cannot be empty.")

    points = _points(rows)
    observations = build_experiment_observations(points, horizon_days=spec.horizon_days)
    if len(observations) < 30:
        raise ValueError("Experiment #001 requires at least 30 constructed observations.")

    content_hash = dataset_content_hash(rows)
    source_ids = sorted({row.source_id for row in rows})
    source_versions = sorted({row.source_version for row in rows})
    methodology_versions = sorted({row.methodology_version for row in rows})
    if len(source_ids) != 1 or len(source_versions) != 1 or len(methodology_versions) != 1:
        raise ValueError(
            "EXP-001 requires one source_id, source_version, and methodology_version per run."
        )

    manifest = build_dataset_manifest(
        dataset_id=f"EXP-001-{content_hash[:16]}",
        source_id=source_ids[0],
        source_version=source_versions[0],
        methodology_version=methodology_versions[0],
        schema_version=SCHEMA_VERSION,
        content_hash=content_hash,
        observation_start=rows[0].observed_at,
        observation_end=rows[-1].observed_at,
        row_count=len(rows),
        point_in_time=True,
    )

    result = evaluate_experiment_001(observations, spec=spec)
    result["dataset"] = {
        "manifest": manifest.canonical_payload(),
        "manifest_fingerprint": manifest.fingerprint(),
        "row_count": len(rows),
        "observation_count": len(observations),
        "content_hash": content_hash,
        "point_in_time_validated": True,
        "immutable_input": True,
    }
    result["governance"]["dataset_execution_boundary"] = "authorized_csv_only"
    return result


__all__ = ["run_experiment_001_from_csv"]
