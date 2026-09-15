from app.simulator import run_monte_carlo
from app.skeptic import review


def test_monte_carlo_is_reproducible_and_scenario_complete():
    first = run_monte_carlo(paths=200, horizon_steps=10, seed=7)
    second = run_monte_carlo(paths=200, horizon_steps=10, seed=7)

    # Analytical outputs are reproducible. Identity and event timestamps are intentionally unique per run.
    for result in (first, second):
        result.pop("simulation_id", None)
        result.pop("timestamp", None)
    assert first == second
    assert first["independent_of_agents"] is True
    assert first["valid"] is True
    assert {s["scenario"] for s in first["scenarios"]} == {"base", "bull", "bear", "adversarial"}
    assert all(0.0 <= s["probability_loss"] <= 1.0 for s in first["scenarios"])


def test_skeptic_reviews_distribution_before_synthesis():
    simulation = run_monte_carlo(paths=200, horizon_steps=10, seed=11)
    agents = [{
        "agent_id": "quant",
        "direction": "LONG",
        "confidence": 0.7,
        "evidence": [{"evidence_id": "e1"}],
    }]

    result = review(agents, simulation)

    assert result["status"] == "reviewed"
    assert result["recommendation"] in {"hold", "proceed_to_synthesis"}
