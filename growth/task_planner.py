"""Plan and persist the next research task from known evidence."""

from __future__ import annotations

from .next_task import next_research_task
from .qualification import SignalCategory
from .research_tasks import ResearchTask
from .task_store import ResearchTaskStore


def refresh_research_task(
    store: ResearchTaskStore,
    prospect_id: str,
    known: set[SignalCategory],
) -> ResearchTask | None:
    task = next_research_task(prospect_id, known)
    if task is None:
        store.clear(prospect_id)
        return None
    return store.set(task)
