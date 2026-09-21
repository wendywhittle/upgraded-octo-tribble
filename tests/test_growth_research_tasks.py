import pytest

from growth.research_tasks import build_research_task


def test_build_research_task_is_deterministic():
    task = build_research_task(
        "ATG-VIKING-000001",
        "https://www.vikingprt.com/investment-strategy/",
        "Viking Partners acquisition strategy industrial",
        "Establish current acquisition fit",
    )

    assert task.prospect_id == "ATG-VIKING-000001"
    assert task.target == "https://www.vikingprt.com/investment-strategy/"
    assert task.query == "Viking Partners acquisition strategy industrial"
    assert task.purpose == "Establish current acquisition fit"


def test_build_research_task_rejects_missing_target():
    with pytest.raises(ValueError):
        build_research_task("ATG-000001", "", "query", "purpose")
