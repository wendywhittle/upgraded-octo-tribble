from pathlib import Path

from growth.loop import run_once
from growth.research import ResearchObservation
from growth.state import GrowthStore


def test_run_once_persists_observation_and_progresses(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create(
        "ATG-LOOP-000001",
        "Loop Prospect",
        {"evidence": ["documented"]},
        "Research prospect",
    )
    store.transition("ATG-LOOP-000001", "RESEARCH", "Research prospect")

    observation = ResearchObservation(
        prospect_id="ATG-LOOP-000001",
        source="fixture",
        observed_at="2026-09-21T00:00:00+00:00",
        facts=("documented acquisition criterion",),
    )

    result = run_once(
        store,
        "ATG-LOOP-000001",
        str(tmp_path / "observations.jsonl"),
        observation,
    )

    assert result.progressed is True
    assert result.observation == observation
    assert result.work is not None
    assert result.work.state == "QUALIFY"

    lines = (tmp_path / "observations.jsonl").read_text().splitlines()
    assert len(lines) == 1
    assert "documented acquisition criterion" in lines[0]


def test_run_once_is_blocked_without_research_observation(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create("ATG-LOOP-000002", "Blocked Prospect", {}, "Research")
    store.transition("ATG-LOOP-000002", "RESEARCH", "Research")

    result = run_once(
        store,
        "ATG-LOOP-000002",
        str(tmp_path / "observations.jsonl"),
    )

    assert result.progressed is False
    assert result.work is not None
    assert result.work.state == "RESEARCH"
