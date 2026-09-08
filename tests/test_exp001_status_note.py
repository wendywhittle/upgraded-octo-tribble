from pathlib import Path


def test_exp001_status_note():
    text = Path("docs/EXP-001_STATUS_NOTE.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "no empirical conclusion" in text
