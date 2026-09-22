"""Bounded worker that resumes a prospect from persistent state.

This worker chooses the next action from stored state and, when available,
exposes the durable research task as the unit of work. It does not contact
external parties and never changes investment decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state import GrowthStore
from .task_store import ResearchTaskStore


@dataclass(frozen=True)
class WorkItem:
    prospect_id: str
    state: str
    action: str
    requires_human_approval: bool
    research_task: object | None = None


def next_work(
    store: GrowthStore,
    prospect_id: str,
    task_store: ResearchTaskStore | None = None,
) -> WorkItem | None:
    prospect = store.get(prospect_id)
    if prospect is None or prospect.current_state in {"CONVERTED", "STOPPED"}:
        return None

    research_task = None
    action = prospect.next_action
    if task_store is not None and prospect.current_state == "RESEARCH":
        research_task = task_store.get(prospect_id)
        if research_task is not None:
            action = research_task.purpose

    approval = prospect.current_state in {
        "CONTACT", "OUTREACH", "RESPOND", "FOLLOW_UP"
    }
    return WorkItem(
        prospect_id=prospect.prospect_id,
        state=prospect.current_state,
        action=action,
        requires_human_approval=approval,
        research_task=research_task,
    )
