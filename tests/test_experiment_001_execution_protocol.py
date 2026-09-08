from pathlib import Path


def test_exp001_protocol_requires_authorized_data_and_human_authority():
    text = Path("docs/EXP-001_EXECUTION_PROTOCOL.md").read_text().lower()
    assert "authorized spx/vix/skew historical export" in text
    assert "synthetic fixtures are mechanics-only" in text
    assert "research-only" in text
    assert "human authorization" in text
