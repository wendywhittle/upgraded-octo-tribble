from pathlib import Path

from growth.state import GrowthStore
from growth.worker import next_work


def test_worker_resumes_next_action_without_conversation_context(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-VIKING-000001",
        "Viking Partners",
        {"qualification": {"status": "QUALIFIED"}},
        "Prepare a human-reviewed acquisition introduction",
    )
    store.transition(
        "ATG-VIKING-000001",
        "RESEARCH",
        "Identify acquisition decision-maker",
    )
    store.transition(
        "ATG-VIKING-000001",
        "QUALIFY",
        "Prepare a human-reviewed acquisition introduction",
    )

    work = next_work(store, "ATG-VIKING-000001")

    assert work is not None
    assert work.state == "QUALIFY"
    assert work.action == "Prepare a human-reviewed acquisition introduction"
    assert work.requires_human_approval is False
