"""Adversarial review of agent conclusions and simulation distributions."""

from typing import Any, Dict, List


def review(agents: List[Dict[str, Any]], simulation: Dict[str, Any]) -> Dict[str, Any]:
    challenges: List[str] = []

    no_data = [a for a in agents if a.get("direction") == "NO_DATA"]
    if no_data:
        challenges.append("One or more agents report NO_DATA; conclusions must not be treated as evidence.")

    if not simulation.get("independent_of_agents", False):
        challenges.append("Simulation independence is not established.")

    scenarios = {s["scenario"]: s for s in simulation.get("scenarios", [])}
    bear = scenarios.get("bear")
    adversarial = scenarios.get("adversarial")
    if bear and bear["probability_loss"] > 0.50:
        challenges.append("Bear scenario has greater than 50% modeled probability of loss.")
    if adversarial and adversarial["p05_terminal"] < scenarios.get("base", adversarial)["p05_terminal"]:
        challenges.append("Adversarial tail materially worsens the lower-tail outcome.")

    # Missing evidence is a first-class challenge rather than an invitation to infer.
    if any(not a.get("evidence") for a in agents if a.get("direction") != "NO_DATA"):
        challenges.append("At least one active agent lacks explicit evidence provenance.")

    recommendation = "no_data" if no_data and len(no_data) == len(agents) else (
        "hold" if challenges else "proceed_to_synthesis"
    )
    status = "insufficient_data" if recommendation == "no_data" else "reviewed"

    return {
        "status": status,
        "challenge_count": len(challenges),
        "challenges": challenges,
        "recommendation": recommendation,
    }
