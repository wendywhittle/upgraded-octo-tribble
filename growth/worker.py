"""Bounded worker that resumes a prospect from persistent state.

This worker chooses the next action from stored state. It does not contact
external parties and never changes investment decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state import GrowthStore, Prospect


@dataclass(frozen=True)
class WorkItem:
    prospect_id: str
    state: str
    action: str
    requires_human_approval: bool


def next_work(store: GrowthStore, prospect_id: str) -> WorkItem | None:
    prospect = store.get(prospect_id)
    if prospect is None or prospect.current_state in {"CONVERTED", "STOPPED"}:
        return None

    approval = prospect.current_state in {"CONTACT", "OUTREACH", "RESPOND", "FOLLOW_UP"}
    return WorkItem(
        prospect_id=prospect.prospect_id,
        state=prospect.current_state,
        action=prospect.next_action,
        requires_human_approval=approval,
    )
