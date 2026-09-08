from pathlib import Path


def test_runbook_contains_authorized_data_and_safety_boundary():
    text = Path("docs/EXP-001_EXECUTION_RUNBOOK.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "research-only" in text
    assert "no live execution" in text
