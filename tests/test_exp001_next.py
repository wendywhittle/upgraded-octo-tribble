from pathlib import Path


def test_exp001_next_step_is_real_data():
    text = Path("docs/EXP-001_NEXT.md").read_text().lower()
    assert "authorized historical spx/vix/skew dataset" in text
    assert "synthetic fixtures remain mechanics-only" in text
