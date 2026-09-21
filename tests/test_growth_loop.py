from pathlib import Path

from growth.loop import run_once
from growth.state import GrowthStore


def test_run_once_resumes_and_progresses(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-LOOP-000001",
        "Loop Prospect",
        {"evidence": ["documented"]},
        "Research prospect",
    )
    store.transition("ATG-LOOP-000001", "RESEARCH", "Research prospect")

    result = run_once(store, "ATG-LOOP-000001")

    assert result.progressed is True
    assert result.work is not None
    assert result.work.state == "QUALIFY"


def test_run_once_does_not_cross_outreach_boundary(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-LOOP-000002",
        "Approval Prospect",
        {},
        "Prepare human-reviewed introduction",
    )
    store.transition(
        "ATG-LOOP-000002",
        "RESEARCH",
        "Research",
    )
    store.transition(
        "ATG-LOOP-000002",
        "QUALIFY",
        "Evaluate fit",
    )
    store.transition(
        "ATG-LOOP-000002",
        "CONTACT",
        "Prepare contact",
    )
    store.transition(
        "ATG-LOOP-000002",
        "OUTREACH",
        "Send introduction only after approval",
    )

    result = run_once(store, "ATG-LOOP-000002")

    assert result.progressed is False
    assert result.work is not None
    assert result.work.state == "OUTREACH"
