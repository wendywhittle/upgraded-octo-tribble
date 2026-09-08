from pathlib import Path


def test_exp001_status_requires_authorized_dataset_before_conclusion():
    text = Path("docs/EXP-001_STATUS.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "no empirical conclusion is valid" in text
