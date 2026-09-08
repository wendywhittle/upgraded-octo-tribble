from app.main import detect_conflicts, simulate, synthesize
from app.schemas import SimulationRequest


def test_simulation_exposes_governance_boundary():
    payload = simulate(SimulationRequest(
        question="Test governance boundary",
        horizon_steps=10,
        paths=200,
        seed=19,
    ))

    assert payload["governance"]["human_decision_required"] is True
    assert payload["governance"]["autonomous_execution"] is False
    assert payload["governance"]["brokerage_connectivity"] is False
    assert payload["breaker"]["human_decision_required"] is True


def test_no_data_survives_to_synthesis():
    agents = [{
        "agent_id": "researcher",
        "direction": "NO_DATA",
        "confidence": 0.0,
        "evidence": [],
        "horizon": "medium",
    }]
    conflicts = detect_conflicts(agents)
    skeptic = {"recommendation": "proceed_to_synthesis"}

    result = synthesize(agents, conflicts, skeptic)

    assert result["verdict"] == "NO_DATA"


def test_same_horizon_disagreement_is_not_averaged_away():
    agents = [
        {"agent_id": "bull", "direction": "LONG", "confidence": 0.8, "horizon": "medium"},
        {"agent_id": "bear", "direction": "SHORT", "confidence": 0.8, "horizon": "medium"},
    ]

    conflicts = detect_conflicts(agents)

    assert len(conflicts["conflicts"]) == 1
    assert conflicts["conflicts"][0]["type"] == "same_horizon_conflict"


def test_different_horizons_are_recorded_separately():
    agents = [
        {"agent_id": "bull", "direction": "LONG", "confidence": 0.8, "horizon": "long"},
        {"agent_id": "bear", "direction": "SHORT", "confidence": 0.8, "horizon": "short"},
    ]

    conflicts = detect_conflicts(agents)

    assert conflicts["conflicts"] == []
    assert len(conflicts["horizon_divergences"]) == 1
    assert conflicts["horizon_divergences"][0]["type"] == "horizon_divergence"
