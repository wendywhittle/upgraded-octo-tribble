from pathlib import Path

import pytest

from growth.state import GrowthStore


def test_prospect_state_survives_store_reopen(tmp_path: Path):
    db_path = tmp_path / "growth.db"

    first = GrowthStore(str(db_path))
    first.create(
        "ATG-000001",
        "Example Capital",
        {"evidence": ["public acquisition criteria"]},
        "Research acquisition criteria",
    )
    first.transition("ATG-000001", "RESEARCH", "Identify acquisition decision-maker")

    second = GrowthStore(str(db_path))
    prospect = second.get("ATG-000001")

    assert prospect is not None
    assert prospect.current_state == "RESEARCH"
    assert prospect.next_action == "Identify acquisition decision-maker"


def test_invalid_transition_is_rejected(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create("ATG-000002", "Example Capital", {}, "Research")

    with pytest.raises(ValueError):
        store.transition("ATG-000002", "CONVERTED", "Done")
