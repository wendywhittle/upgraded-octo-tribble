from pathlib import Path


def test_execution_checklist_preserves_empirical_evidence_boundary():
    text = Path("docs/EXP-001_EXECUTION_CHECKLIST.md").read_text()
    assert "authorized export or licensed feed" in text
    assert "No synthetic fixture is presented as empirical evidence." in text
    assert "Human authority remains required" in text
