"""Strict CSV ingestion boundary for authorized EXP-001 historical data.

This module deliberately accepts provider-exported files rather than fetching
from vendors. It validates the audit fields required by the experiment's
point-in-time boundary and never mutates or executes against external systems.
"""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


REQUIRED_COLUMNS = (
    "observed_at",
    "available_at",
    "source_id",
    "source_version",
    "methodology_version",
    "content_hash",
    "spx_close",
    "vix_close",
    "skew_close",
)


@dataclass(frozen=True)
class HistoricalRow:
    observed_at: str
    available_at: str
    source_id: str
    source_version: str
    methodology_version: str
    content_hash: str
    spx_close: float
    vix_close: float
    skew_close: float


def _timestamp(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc


def parse_csv(text: str) -> tuple[HistoricalRow, ...]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV must include a header")
    missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    rows: list[HistoricalRow] = []
    seen: set[str] = set()
    for number, raw in enumerate(reader, start=2):
        if any(not (raw.get(column) or "").strip() for column in REQUIRED_COLUMNS):
            raise ValueError(f"row {number} has missing required provenance/data")
        observed = _timestamp(raw["observed_at"], "observed_at")
        available = _timestamp(raw["available_at"], "available_at")
        if available > observed:
            raise ValueError(f"row {number} violates point-in-time availability")
        if raw["observed_at"] in seen:
            raise ValueError(f"duplicate observed_at at row {number}")
        seen.add(raw["observed_at"])
        try:
            values = tuple(float(raw[name]) for name in ("spx_close", "vix_close", "skew_close"))
        except ValueError as exc:
            raise ValueError(f"row {number} contains a non-numeric market value") from exc
        if any(value <= 0 for value in values):
            raise ValueError(f"row {number} contains a non-positive market value")
        rows.append(HistoricalRow(
            observed_at=raw["observed_at"], available_at=raw["available_at"],
            source_id=raw["source_id"], source_version=raw["source_version"],
            methodology_version=raw["methodology_version"], content_hash=raw["content_hash"],
            spx_close=values[0], vix_close=values[1], skew_close=values[2],
        ))
    rows.sort(key=lambda row: _timestamp(row.observed_at, "observed_at"))
    return tuple(rows)


def canonical_csv(rows: Iterable[HistoricalRow]) -> str:
    ordered = sorted(rows, key=lambda row: _timestamp(row.observed_at, "observed_at"))
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(REQUIRED_COLUMNS)
    for row in ordered:
        writer.writerow([row.observed_at, row.available_at, row.source_id,
                         row.source_version, row.methodology_version, row.content_hash,
                         f"{row.spx_close:.12g}", f"{row.vix_close:.12g}", f"{row.skew_close:.12g}"])
    return output.getvalue()


def dataset_content_hash(rows: Iterable[HistoricalRow]) -> str:
    return hashlib.sha256(canonical_csv(rows).encode("utf-8")).hexdigest()


__all__ = ["HistoricalRow", "REQUIRED_COLUMNS", "parse_csv", "canonical_csv", "dataset_content_hash"]
