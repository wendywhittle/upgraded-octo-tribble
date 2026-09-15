from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_consolidated_workstation_is_presentation_only():
    js = (ROOT / "web" / "workstation.js").read_text()
    forbidden = ("/trade", "/execute", "/broker", "/transfer", "/portfolio/mutate")
    assert not any(route in js for route in forbidden)


def test_consolidated_workstation_surfaces_truthful_boundary():
    js = (ROOT / "web" / "workstation.js").read_text()
    assert "READY FOR HUMAN AUTHORITY ≠ AUTHORIZED ≠ EXECUTED" in js
    assert "NO DATA" in js
    assert "NOT EXPOSED" in js


def test_consolidated_workstation_uses_single_interaction_layer():
    index = (ROOT / "web" / "index.html").read_text()
    assert "/web/workstation.js" in index
    assert "/web/workstation-v3.js" not in index
    assert "/web/workstation-v4.js" not in index
    assert "/web/workstation-v5.js" not in index
