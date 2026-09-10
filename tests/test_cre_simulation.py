from app.cre_simulation import CRESimulationRequest


def test_cre_simulation_boundary_preserves_missing_values():
    request = CRESimulationRequest("deal-1", {"purchase_price": 10_000_000, "noi": None})
    assert request.missing_variables() == ("noi",)
    assert request.is_ready() is False
    assert request.assumption_labels() == ("purchase_price=10000000",)


def test_cre_simulation_boundary_declares_required_scenarios():
    request = CRESimulationRequest("deal-1", {"purchase_price": 10_000_000, "noi": 650_000})
    assert request.is_ready()
    assert "TAIL RISK" in request.scenario_names
