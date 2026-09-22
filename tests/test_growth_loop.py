from pathlib import Path

from growth.loop import run_once
from growth.qualification import SignalCategory
from growth.research import ResearchObservation
from growth.research_adapter import ResearchSignal
from growth.state import GrowthStore
from growth.task_store import ResearchTaskStore


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
    signals = (
        ResearchSignal(SignalCategory.ACQUISITION_APPETITE, "Active acquisition appetite."),
        ResearchSignal(SignalCategory.ASSET_FIT, "Relevant asset fit."),
    )

    result = run_once(
        store,
        "ATG-LOOP-000001",
        str(tmp_path / "observations.jsonl"),
        observation,
        signals,
        ResearchTaskStore(str(tmp_path / "growth.db")),
    )

    assert result.progressed is True
    assert result.observation == observation
    assert result.work is not None
    assert result.work.state == "QUALIFY"

    lines = (tmp_path / "observations.jsonl").read_text().splitlines()
    assert len(lines) == 1
    assert "documented acquisition criterion" in lines[0]


def test_run_once_keeps_research_when_evidence_gap_has_next_task(tmp_path: Path):
    db_path = str(tmp_path / "growth.db")
    store = GrowthStore(db_path)
    store.create("ATG-LOOP-000002", "Gap Prospect", {}, "Research")
    store.transition("ATG-LOOP-000002", "RESEARCH", "Research")

    observation = ResearchObservation(
        prospect_id="ATG-LOOP-000002",
        source="fixture",
        observed_at="2026-09-21T00:00:00+00:00",
        facts=("recent activity",),
    )
    signals = (
        ResearchSignal(SignalCategory.RECENT_ACTIVITY, "Recent activity."),
    )
    tasks = ResearchTaskStore(db_path)

    result = run_once(
        store,
        "ATG-LOOP-000002",
        str(tmp_path / "observations.jsonl"),
        observation,
        signals,
        tasks,
    )

    current = store.get("ATG-LOOP-000002")
    assert result.progressed is False
    assert current is not None
    assert current.current_state == "RESEARCH"
    assert result.work is not None
    assert result.work.state == "RESEARCH"
    assert result.work.research_task is not None
    assert result.work.action == result.work.research_task.purpose


def test_run_once_is_blocked_without_research_observation(tmp_path: Path):
    store = GrowthStore(str(tmp_path / "growth.db"))
    store.create("ATG-LOOP-000003", "Blocked Prospect", {}, "Research")
    store.transition("ATG-LOOP-000003", "RESEARCH", "Research")

    result = run_once(
        store,
        "ATG-LOOP-000003",
        str(tmp_path / "observations.jsonl"),
    )

    assert result.progressed is False
    assert result.work is not None
    assert result.work.state == "RESEARCH"
