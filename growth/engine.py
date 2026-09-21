"""Deterministic progression from explicit research observations."""

from __future__ import annotations

from .state import GrowthStore, Prospect


def advance_from_research(
    store: GrowthStore,
    prospect_id: str,
    *,
    sufficient_evidence: bool,
) -> Prospect:
    """Advance a prospect using an explicit evidence decision.

    The decision is supplied as a factual evaluation result. This function
    performs no external research and no external communication.
    """
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

    return store.transition(
        prospect_id,
        "STOPPED",
        "Insufficient evidence; no further action",
    )
