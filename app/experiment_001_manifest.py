"""Immutable dataset manifest support for Experiment #001.

The manifest is deliberately separate from raw-data acquisition. It identifies the
exact dataset and methodology used by a research run without storing credentials,
provider-specific clients, or executable trading capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping


REQUIRED_SERIES = ("spx_close", "vix_close", "skew_close")


@dataclass(frozen=True)
class Experiment001DatasetManifest:
    dataset_id: str
    source_id: str
    source_version: str
    methodology_version: str
    schema_version: str
    content_hash: str
    observation_start: str
    observation_end: str
    row_count: int
    point_in_time: bool = True

    def canonical_payload(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "methodology_version": self.methodology_version,
            "schema_version": self.schema_version,
            "content_hash": self.content_hash,
            "observation_start": self.observation_start,
            "observation_end": self.observation_end,
            "row_count": self.row_count,
            "point_in_time": self.point_in_time,
        }

    def fingerprint(self) -> str:
        payload = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_dataset_manifest(
    *,
    dataset_id: str,
    source_id: str,
    source_version: str,
    methodology_version: str,
    schema_version: str,
    content_hash: str,
    observation_start: str,
    observation_end: str,
    row_count: int,
    point_in_time: bool = True,
) -> Experiment001DatasetManifest:
    """Build and validate an immutable identity for an EXP-001 dataset."""
    values = {
        "dataset_id": dataset_id,
        "source_id": source_id,
        "source_version": source_version,
        "methodology_version": methodology_version,
        "schema_version": schema_version,
        "content_hash": content_hash,
        "observation_start": observation_start,
        "observation_end": observation_end,
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")
    if row_count <= 0:
        raise ValueError("row_count must be positive")
    if not point_in_time:
        raise ValueError("Experiment #001 requires point-in-time data")
    if len(content_hash) != 64 or any(ch not in "0123456789abcdef" for ch in content_hash.lower()):
        raise ValueError("content_hash must be a SHA-256 hex digest")
    return Experiment001DatasetManifest(
        dataset_id=dataset_id,
        source_id=source_id,
        source_version=source_version,
        methodology_version=methodology_version,
        schema_version=schema_version,
        content_hash=content_hash.lower(),
        observation_start=observation_start,
        observation_end=observation_end,
        row_count=row_count,
        point_in_time=point_in_time,
    )


def fingerprint_rows(rows: list[Mapping[str, object]]) -> str:
    """Return a deterministic hash of canonicalized source rows.

    Raw values are hashed exactly as represented after JSON normalization. This is
    an identity primitive, not a data-cleaning or transformation step.
    """
    canonical = json.dumps(list(rows), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
