from pathlib import Path


def test_exp001_execution_protocol_is_research_only():
    text = Path("docs/EXP-001_EXECUTION.md").read_text()
    assert "research-only" in text.lower()
    assert "does not place trades" in text.lower()
    assert "human authorization" in text.lower()


def test_exp001_execution_protocol_requires_authorized_historical_data():
    text = Path("docs/EXP-001_EXECUTION.md").read_text()
    assert "authorized export or licensed feed" in text
    assert "point-in-time" in text.lower()
    assert "immutable dataset content hash" in text.lower()
