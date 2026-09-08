from pathlib import Path


def test_data_handoff_requires_authorized_source():
    text = Path("docs/EXP-001_DATA_HANDOFF.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "do not use synthetic or unverified data" in text
