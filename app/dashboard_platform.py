"""Canonical AletheiaTelos interactive dashboard platform contract.

The machine-readable source of truth lives at web/dashboard-source-of-truth.json.
This module provides a small typed access boundary for backend code and tests
without creating a second dashboard specification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SOURCE_OF_TRUTH_PATH = (
    Path(__file__).resolve().parent.parent / "web" / "dashboard-source-of-truth.json"
)


def load_dashboard_platform() -> dict[str, Any]:
    """Load the canonical dashboard platform contract."""
    with SOURCE_OF_TRUTH_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dashboard_pipeline() -> list[dict[str, Any]]:
    """Return the canonical 11-stage dashboard pipeline."""
    return list(load_dashboard_platform()["pipeline"])


def dashboard_authority_contract() -> dict[str, bool]:
    """Return the dashboard interaction/authority boundary contract."""
    return dict(load_dashboard_platform()["interaction_contract"])
