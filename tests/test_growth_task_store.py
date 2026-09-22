from growth.research_tasks import build_research_task
from growth.task_store import ResearchTaskStore


def test_research_task_survives_store_reopen(tmp_path):
    path = str(tmp_path / "growth.db")
    task = build_research_task(
        "ATG-000001",
        "investment strategy",
        "current acquisition criteria",
        "Establish acquisition appetite",
    )

    ResearchTaskStore(path).set(task)
    reopened = ResearchTaskStore(path)

    assert reopened.get("ATG-000001") == task


def test_research_task_can_be_replaced_and_cleared(tmp_path):
    path = str(tmp_path / "growth.db")
    store = ResearchTaskStore(path)

    first = build_research_task(
        "ATG-000001", "strategy", "acquisition criteria", "appetite"
    )
    second = build_research_task(
        "ATG-000001", "team", "acquisitions contact", "decision maker"
    )

    store.set(first)
    store.set(second)
    assert store.get("ATG-000001") == second

    store.clear("ATG-000001")
    assert store.get("ATG-000001") is None
