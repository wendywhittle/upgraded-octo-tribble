"""One-step autonomous dry-run loop for the Growth Engine experiment."""

from __future__ import annotations

from dataclasses import dataclass

from .engine import advance_from_research
from .research import ResearchObservation, append_observation
from .state import GrowthStore
from .worker import WorkItem, next_work


@dataclass(frozen=True)
class LoopResult:
    work: WorkItem | None
    progressed: bool
    observation: ResearchObservation | None = None


def run_once(
    store: GrowthStore,
    prospect_id: str,
    observation_path: str,
    observation: ResearchObservation | None = None,
) -> LoopResult:
    """Resume one prospect using only explicitly supplied research.

    No web access, messaging, or external side effects occur here. Research
    must be supplied as an observation, then the state transition is
    deterministic from that observation.
    """
    work = next_work(store, prospect_id)
    if work is None:
        return LoopResult(None, False)

    if work.state != "RESEARCH":
        return LoopResult(work, False)

    if observation is None:
        return LoopResult(work, False)

    if observation.prospect_id != prospect_id:
        raise ValueError("observation prospect_id does not match prospect")

    append_observation(observation_path, observation)
    sufficient = bool(observation.facts)
    result = advance_from_research(store, prospect_id, sufficient_evidence=sufficient)

    return LoopResult(
        next_work(store, prospect_id),
        result.current_state != "RESEARCH",
        observation,
    )
