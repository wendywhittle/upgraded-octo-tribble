from growth.loop import run_once
from growth.qualification import SignalCategory
from growth.research import ResearchObservation
from growth.research_adapter import ResearchSignal
from growth.state import GrowthStore
from growth.task_store import ResearchTaskStore


def test_loop_persists_next_task_when_evidence_is_incomplete(tmp_path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create("ATG-000001", "Example", {}, "Research")
    store.transition("ATG-000001", "RESEARCH", "Research")
    tasks = ResearchTaskStore(str(tmp_path / "growth.db"))

    result = run_once(
        store,
        "ATG-000001",
        str(tmp_path / "observations.jsonl"),
        ResearchObservation(
            "ATG-000001", "fixture", "2026-09-21",
            ("recent activity observed",),
        ),
        (ResearchSignal(SignalCategory.RECENT_ACTIVITY, "recent activity observed"),),
        tasks,
    )

    assert result.progressed is False
    assert store.get("ATG-000001").current_state == "RESEARCH"
    assert tasks.get("ATG-000001") is not None


def test_loop_clears_task_when_qualification_is_complete(tmp_path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create("ATG-000002", "Example", {}, "Research")
    store.transition("ATG-000002", "RESEARCH", "Research")
    tasks = ResearchTaskStore(str(tmp_path / "growth.db"))
    tasks.set(__import__("growth.next_task", fromlist=["next_research_task"]).next_research_task("ATG-000002", set()))

    signals = (
        ResearchSignal(SignalCategory.ACQUISITION_APPETITE, "actively acquiring"),
        ResearchSignal(SignalCategory.ASSET_FIT, "industrial"),
    )
    result = run_once(
        store,
        "ATG-000002",
        str(tmp_path / "observations.jsonl"),
        ResearchObservation("ATG-000002", "fixture", "2026-09-21", ("fit observed",)),
        signals,
        tasks,
    )

    assert result.progressed is True
    assert store.get("ATG-000002").current_state == "QUALIFY"
    assert tasks.get("ATG-000002") is None
