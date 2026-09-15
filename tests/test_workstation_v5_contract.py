from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_workstation_v5_is_presentation_only():
    js = (ROOT / "web" / "workstation-v5.js").read_text()
    forbidden = ("/trade", "/execute", "/broker", "/transfer", "/portfolio/mutate")
    assert not any(route in js for route in forbidden)


def test_workstation_v5_surfaces_truthful_boundary():
    js = (ROOT / "web" / "workstation-v5.js").read_text()
    assert "READY FOR HUMAN AUTHORITY ≠ AUTHORIZED ≠ EXECUTED" in js
    assert "NO DATA" in js
    assert "NOT EXPOSED" in js


def test_workstation_v5_uses_delegated_dynamic_interaction():
    js = (ROOT / "web" / "workstation-v5.js").read_text()
    assert "pipeline.addEventListener('click'" in js
    assert "root.addEventListener('click'" in js
