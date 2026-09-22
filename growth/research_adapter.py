"""Controlled adapter from externally gathered research into typed signals."""

from __future__ import annotations

from dataclasses import dataclass

from growth.qualification import SignalCategory
from growth.research import ResearchObservation


@dataclass(frozen=True)
class ResearchSignal:
    category: SignalCategory
    fact: str


def adapt_observation(
    observation: ResearchObservation,
    signals: tuple[ResearchSignal, ...],
) -> tuple[ResearchSignal, ...]:
    if not observation.prospect_id:
        raise ValueError("observation prospect_id is required")
    if any(not signal.fact.strip() for signal in signals):
        raise ValueError("signal fact is required")
    return tuple(signals)


def signal_categories(
    signals: tuple[ResearchSignal, ...],
) -> set[SignalCategory]:
    return {signal.category for signal in signals}
