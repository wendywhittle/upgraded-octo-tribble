"""One-step autonomous dry-run loop for the Growth Engine experiment."""

from __future__ import annotations

from dataclasses import dataclass

from .engine import advance_from_research
from .qualification import evaluate_qualification
from .research import ResearchObservation, append_observation
from .research_adapter import ResearchSignal, signal_categories
from .state import GrowthStore
from .task_planner import refresh_research_task
from .task_store import ResearchTaskStore
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
    signals: tuple[ResearchSignal, ...] = (),
    task_store: ResearchTaskStore | None = None,
) -> LoopResult:
    """Resume one prospect using explicitly supplied research and signals.

    No web access, messaging, or external side effects occur here. Progression
    requires typed evidence so free-form text alone cannot qualify a prospect.
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
    categories = signal_categories(signals)
    qualification = evaluate_qualification(categories)

    if task_store is not None:
        refresh_research_task(task_store, prospect_id, categories)

    result = advance_from_research(
        store,
        prospect_id,
        sufficient_evidence=qualification.qualified,
    )

    return LoopResult(
        next_work(store, prospect_id),
        result.current_state != "RESEARCH",
        observation,
    )
