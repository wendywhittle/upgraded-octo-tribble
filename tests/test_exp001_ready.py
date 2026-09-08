from pathlib import Path


def test_exp001_ready_state_requires_real_authorized_data():
    text = Path("docs/EXP-001_READY.md").read_text().lower()
    assert "authorized spx/vix/skew historical dataset" in text
    assert "no synthetic fixture" in text
    assert "research-only" in text
