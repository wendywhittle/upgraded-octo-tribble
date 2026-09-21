from pathlib import Path

from growth.engine import advance_from_research
from growth.state import GrowthStore


def test_sufficient_research_advances_without_conversation(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-VIKING-000001",
        "Viking Partners",
        {"evidence": ["industrial"]},
        "Research acquisition criteria",
    )
    store.transition(
        "ATG-VIKING-000001",
        "RESEARCH",
        "Research acquisition criteria",
    )

    result = advance_from_research(
        store,
        "ATG-VIKING-000001",
        sufficient_evidence=True,
    )

    assert result.current_state == "QUALIFY"
    assert result.next_action == (
        "Evaluate fit and prepare the next human-reviewed task"
    )


def test_insufficient_research_stops(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-STOP-000001",
        "Insufficient Evidence",
        {},
        "Research",
    )
    store.transition("ATG-STOP-000001", "RESEARCH", "Research")

    result = advance_from_research(
        store,
        "ATG-STOP-000001",
        sufficient_evidence=False,
    )

    assert result.current_state == "STOPPED"
