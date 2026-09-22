from growth.next_task import next_research_task
from growth.qualification import SignalCategory


def test_next_task_fills_missing_acquisition_evidence_first():
    task = next_research_task("ATG-000001", set())

    assert task is not None
    assert task.target == "current acquisition strategy"


def test_next_task_moves_to_fit_after_acquisition_evidence():
    task = next_research_task(
        "ATG-000001",
        {SignalCategory.ACQUISITION_APPETITE},
    )

    assert task is not None
    assert task.target == "investment criteria"


def test_next_task_identifies_contact_after_fit_is_known():
    task = next_research_task(
        "ATG-000001",
        {
            SignalCategory.ACQUISITION_APPETITE,
            SignalCategory.ASSET_FIT,
        },
    )

    assert task is not None
    assert task.target == "acquisitions contact"


def test_next_task_stops_when_required_research_is_complete():
    task = next_research_task(
        "ATG-000001",
        {
            SignalCategory.ACQUISITION_APPETITE,
            SignalCategory.ASSET_FIT,
            SignalCategory.DECISION_MAKER,
        },
    )

    assert task is None
