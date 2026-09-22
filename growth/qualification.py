"""Deterministic qualification policy for research observations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalCategory(str, Enum):
    ACQUISITION_APPETITE = "ACQUISITION_APPETITE"
    ASSET_FIT = "ASSET_FIT"
    GEOGRAPHIC_FIT = "GEOGRAPHIC_FIT"
    DEAL_SIZE_FIT = "DEAL_SIZE_FIT"
    DECISION_MAKER = "DECISION_MAKER"
    RECENT_ACTIVITY = "RECENT_ACTIVITY"


@dataclass(frozen=True)
class QualificationResult:
    qualified: bool
    matched: tuple[SignalCategory, ...]
    missing: tuple[SignalCategory, ...]


def evaluate_qualification(
    categories: set[SignalCategory],
    required_fit: set[SignalCategory] | None = None,
) -> QualificationResult:
    required_fit = required_fit or {
        SignalCategory.ASSET_FIT,
        SignalCategory.GEOGRAPHIC_FIT,
        SignalCategory.DEAL_SIZE_FIT,
    }
    matched = tuple(sorted(categories & required_fit, key=lambda item: item.value))
    missing = tuple(sorted(required_fit - categories, key=lambda item: item.value))
    qualified = (
        SignalCategory.ACQUISITION_APPETITE in categories
        and bool(matched)
    )
    return QualificationResult(
        qualified=qualified,
        matched=matched,
        missing=missing,
    )
