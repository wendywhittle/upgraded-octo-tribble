from growth.next_task import next_research_task
from growth.qualification import SignalCategory
from growth.state import GrowthStore
from growth.task_store import ResearchTaskStore
from growth.worker import next_work


def test_worker_uses_persisted_research_task(tmp_path):
    db_path = str(tmp_path / "growth.db")
    store = GrowthStore(db_path)
    store.create("ATG-000003", "Example", {}, "Research")
    store.transition("ATG-000003", "RESEARCH", "Research")

    tasks = ResearchTaskStore(db_path)
    task = next_research_task(
        "ATG-000003",
        {SignalCategory.ACQUISITION_APPETITE},
    )
    tasks.set(task)

    work = next_work(store, "ATG-000003", tasks)

    assert work is not None
    assert work.state == "RESEARCH"
    assert work.research_task == task
    assert work.action == task.purpose
