from growth.next_task import next_research_task
from growth.qualification import SignalCategory
from growth.task_planner import refresh_research_task
from growth.task_store import ResearchTaskStore


def test_planner_persists_next_missing_evidence_task(tmp_path):
    store = ResearchTaskStore(str(tmp_path / "growth.db"))

    task = refresh_research_task(
        store,
        "ATG-000001",
        {SignalCategory.ACQUISITION_APPETITE},
    )

    assert task == next_research_task(
        "ATG-000001",
        {SignalCategory.ACQUISITION_APPETITE},
    )
    assert store.get("ATG-000001") == task


def test_planner_clears_task_when_required_research_is_complete(tmp_path):
    store = ResearchTaskStore(str(tmp_path / "growth.db"))
    store.set(
        next_research_task("ATG-000001", set())
    )

    task = refresh_research_task(
        store,
        "ATG-000001",
        {
            SignalCategory.ACQUISITION_APPETITE,
            SignalCategory.ASSET_FIT,
            SignalCategory.DECISION_MAKER,
        },
    )

    assert task is None
    assert store.get("ATG-000001") is None
