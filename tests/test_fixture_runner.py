from pathlib import Path

from growth.fixture_runner import run_fixture
from growth.state import GrowthStore


def test_fixture_runner_resumes_persisted_prospect(tmp_path: Path):
    db = tmp_path / "growth.db"
    store = GrowthStore(str(db))
    store.create(
        "ATG-VIKING-000001",
        "Viking Partners",
        {"asset_type": "industrial"},
        "Research public acquisition criteria",
    )
    store.transition(
        "ATG-VIKING-000001",
        "RESEARCH",
        "Research public acquisition criteria",
    )
    store.close()

    fixture = Path("growth/fixtures/viking_research_observation.json")
    result = run_fixture(
        str(db),
        str(tmp_path / "observations.jsonl"),
        str(fixture),
    )

    assert result.progressed is True
    assert result.work is not None
    assert result.work.state == "QUALIFY"

    reopened = GrowthStore(str(db))
    prospect = reopened.get("ATG-VIKING-000001")
    assert prospect["current_state"] == "QUALIFY"
