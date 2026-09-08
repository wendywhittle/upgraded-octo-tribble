from pathlib import Path


def test_exp001_execution_boundary_is_research_only():
    text = Path("docs/EXP-001_EXECUTION_BOUNDARY.md").read_text().lower()
    assert "authorized historical" in text
    assert "synthetic fixtures are mechanics-only" in text
    assert "research-only" in text
    assert "human authorization" in text
