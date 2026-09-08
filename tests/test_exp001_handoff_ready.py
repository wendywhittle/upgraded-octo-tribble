from pathlib import Path


def test_exp001_handoff_ready():
    assert "preregistered specification" in Path("docs/EXP-001_HANDOFF_READY.md").read_text().lower()
