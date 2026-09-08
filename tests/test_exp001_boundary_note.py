from pathlib import Path


def test_exp001_boundary_note():
    assert "authorized historical spx/vix/skew dataset" in Path("docs/EXP-001_BOUNDARY_NOTE.md").read_text().lower()
