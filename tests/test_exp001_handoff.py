from pathlib import Path


def test_exp001_handoff_rejects_unverified_substitutes():
    text = Path("docs/EXP-001_HANDOFF.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "do not substitute synthetic or unverified data" in text
