"""Independent Monte Carlo risk engine.

Agent conclusions provide assumptions, never the simulation result itself.
The engine produces distributions across base, bull, bear, and adversarial paths.
"""

import math
import random
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any, Dict, List
from uuid import uuid4


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
    """Run a reproducible, independent simulation with explicit input validation."""
    if not math.isfinite(initial_value) or initial_value <= 0:
        raise ValueError("initial_value must be finite and > 0")
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be >= 1")
    if paths <= 0:
        raise ValueError("paths must be > 0")
    if seed < 0:
        raise ValueError("seed must be >= 0")

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
        "simulation_id": f"SIM-{uuid4().hex}",
        "engine": "AletheiaTelos Independent Monte Carlo Risk Engine v1",
        "methodology": "Monte Carlo geometric path simulation",
        "independent_of_agents": True,
        "independence_metadata": {"agent_conclusions_are_inputs_only": True},
        "valid": True,
        "paths": paths,
        "horizon_steps": horizon_steps,
        "seed": seed,
        "scenarios": summaries,
        "assumptions": assumptions or [
            "Agent conclusions do not determine simulation outcomes.",
            "Scenario parameters are explicit and reproducible.",
            "Distributions are reviewed by the skeptic layer before synthesis.",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }