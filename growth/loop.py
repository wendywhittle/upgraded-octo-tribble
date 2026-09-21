"""One-step autonomous dry-run loop for the Growth Engine experiment."""

from __future__ import annotations

from dataclasses import dataclass

from .engine import advance_from_research
from .state import GrowthStore
from .worker import WorkItem, next_work


@dataclass(frozen=True)
class LoopResult:
    work: WorkItem | None
    progressed: bool


def run_once(store: GrowthStore, prospect_id: str) -> LoopResult:
    """Resume one prospect and perform only safe internal progression.

    RESEARCH is advanced using the stored workflow decision. CONTACT,
    OUTREACH, and FOLLOW_UP never send anything here and remain approval-gated.
    """
    work = next_work(store, prospect_id)
    if work is None:
        return LoopResult(None, False)

    if work.state == "RESEARCH":
        result = advance_from_research(
            store,
            prospect_id,
            sufficient_evidence=True,
        )
        return LoopResult(
            next_work(store, prospect_id),
            result.current_state != "RESEARCH",
        )

    return LoopResult(work, False)
