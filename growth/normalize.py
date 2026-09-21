"""Normalize externally gathered research into the Growth Engine schema."""

from __future__ import annotations

from collections.abc import Iterable

from .research import ResearchObservation


def normalize_observation(
    prospect_id: str,
    source: str,
    observed_at: str,
    facts: Iterable[str],
) -> ResearchObservation:
    normalized = tuple(
        fact.strip()
        for fact in facts
        if fact is not None and fact.strip()
    )
    if not prospect_id.strip():
        raise ValueError("prospect_id is required")
    if not source.strip():
        raise ValueError("source is required")
    if not observed_at.strip():
        raise ValueError("observed_at is required")
    return ResearchObservation(
        prospect_id=prospect_id.strip(),
        source=source.strip(),
        observed_at=observed_at.strip(),
        facts=normalized,
    )
