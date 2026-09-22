"""Deterministic progression from explicit research observations."""

from __future__ import annotations

from .state import GrowthStore, Prospect


def advance_from_research(
    store: GrowthStore,
    prospect_id: str,
    *,
    sufficient_evidence: bool,
    next_research_action: str | None = None,
) -> Prospect:
    """Advance research without terminating solvable evidence gaps."""
    prospect = store.get(prospect_id)
    if prospect is None:
        raise KeyError(prospect_id)
    if prospect.current_state != "RESEARCH":
        raise ValueError(
            f"Expected RESEARCH state, found {prospect.current_state}"
        )

    if sufficient_evidence:
        return store.transition(
            prospect_id,
            "QUALIFY",
            "Evaluate fit and prepare the next human-reviewed task",
        )

    if next_research_action is not None:
        return store.set_next_action(prospect_id, next_research_action)

    return store.transition(
        prospect_id,
        "STOPPED",
        "Insufficient evidence; no further research task available",
    )
