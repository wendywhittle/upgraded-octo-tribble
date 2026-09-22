from growth.loop import run_once
from growth.next_task import next_research_task
from growth.qualification import SignalCategory
from growth.research import ResearchObservation
from growth.research_adapter import ResearchSignal
from growth.state import GrowthStore
from growth.task_store import ResearchTaskStore


def test_incomplete_evidence_keeps_prospect_in_research(tmp_path):
    db_path = str(tmp_path / "growth.db")
    observation_path = str(tmp_path / "observations.jsonl")
    store = GrowthStore(db_path)
    store.create("ATG-000004", "Example", {}, "Begin research")
    store.transition("ATG-000004", "RESEARCH", "Begin research")
    tasks = ResearchTaskStore(db_path)

    observation = ResearchObservation(
        prospect_id="ATG-000004",
        source="fixture",
        observed_at="2026-09-21",
        facts=("Recent activity observed.",),
    )
    signals = (
        ResearchSignal(SignalCategory.RECENT_ACTIVITY, "Recent activity observed."),
    )

    result = run_once(
        store,
        "ATG-000004",
        observation_path,
        observation,
        signals,
        tasks,
    )

    current = store.get("ATG-000004")
    expected = next_research_task(
        "ATG-000004",
        {SignalCategory.RECENT_ACTIVITY},
    )

    assert result.progressed is False
    assert current is not None
    assert current.current_state == "RESEARCH"
    assert current.next_action == expected.purpose
    assert tasks.get("ATG-000004") == expected
