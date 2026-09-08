"""Independent Monte Carlo risk engine.

Agent conclusions provide assumptions, never the simulation result itself.
The engine produces distributions across base, bull, bear, and adversarial paths.
"""

import math
import random
from statistics import mean, median
from typing import Any, Dict, List


SCENARIOS = {
    "base": {"drift": 0.0005, "volatility": 0.012, "shock": 0.0},
    "bull": {"drift": 0.0012, "volatility": 0.014, "shock": 0.0},
    "bear": {"drift": -0.0010, "volatility": 0.018, "shock": 0.0},
    "adversarial": {"drift": -0.0015, "volatility": 0.028, "shock": -0.12},
}


def _drawdown(path: List[float]) -> float:
    peak = path[0]
    worst = 0.0
    for value in path:
        peak = max(peak, value)
        if peak:
            worst = max(worst, (peak - value) / peak)
    return worst


def _percentile(values: List[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def run_monte_carlo(
    initial_value: float = 100.0,
    horizon_steps: int = 60,
    paths: int = 5000,
    seed: int = 42,
    assumptions: List[str] | None = None,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    summaries: List[Dict[str, Any]] = []

    for scenario, params in SCENARIOS.items():
        terminals: List[float] = []
        drawdowns: List[float] = []
        for _ in range(paths):
            value = initial_value
            path = [value]
            for step in range(horizon_steps):
                shock = rng.gauss(0.0, params["volatility"])
                value *= math.exp(params["drift"] - 0.5 * params["volatility"] ** 2 + shock)
                if scenario == "adversarial" and step == horizon_steps // 2:
                    value *= 1.0 + params["shock"]
                path.append(value)
            terminals.append(value)
            drawdowns.append(_drawdown(path))

        summaries.append({
            "scenario": scenario,
            "mean_terminal": round(mean(terminals), 4),
            "median_terminal": round(median(terminals), 4),
            "p05_terminal": round(_percentile(terminals, 0.05), 4),
            "p95_terminal": round(_percentile(terminals, 0.95), 4),
            "probability_loss": round(sum(v < initial_value for v in terminals) / paths, 4),
            "max_drawdown_mean": round(mean(drawdowns), 4),
        })

    return {
        "engine": "AletheiaTelos Independent Monte Carlo Risk Engine v1",
        "independent_of_agents": True,
        "paths": paths,
        "horizon_steps": horizon_steps,
        "seed": seed,
        "scenarios": summaries,
        "assumptions": assumptions or [
            "Agent conclusions do not determine simulation outcomes.",
            "Scenario parameters are explicit and reproducible.",
            "Distributions are reviewed by the skeptic layer before synthesis.",
        ],
    }
