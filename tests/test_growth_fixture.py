import json
from pathlib import Path

from growth.state import GrowthStore


def test_viking_fixture_can_resume_from_persistent_state(tmp_path: Path):
    fixture = json.loads(
        Path("growth/fixtures/viking_partners.json").read_text(encoding="utf-8")
    )
    store = GrowthStore(str(tmp_path / "growth.db"))

    store.create(
        fixture["prospect_id"],
        fixture["account"],
        fixture,
        "Research acquisition criteria",
    )
    store.transition(
        fixture["prospect_id"],
        "RESEARCH",
        "Identify acquisition decision-maker",
    )
    store.transition(
        fixture["prospect_id"],
        "QUALIFY",
        fixture["next_action"],
    )

    reopened = GrowthStore(str(tmp_path / "growth.db"))
    prospect = reopened.get(fixture["prospect_id"])

    assert prospect is not None
    assert prospect.current_state == "QUALIFY"
    assert prospect.next_action == fixture["next_action"]
