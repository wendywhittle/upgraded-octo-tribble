"""Independent Monte Carlo risk engine.

Agent conclusions provide assumptions, never the simulation result itself.
The engine produces distributions across base, bull, bear, adversarial, and tail-risk paths.
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
    "tail_risk": {"drift": -0.0025, "volatility": 0.045, "shock": -0.25},
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
                if scenario in {"adversarial", "tail_risk"} and step == horizon_steps // 2:
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


def run_cre_monte_carlo(
    purchase_price: float | None,
    noi: float | None,
    hold_period: int = 5,
    paths: int = 5000,
    seed: int = 42,
    occupancy: float | None = None,
    rent_growth: float | None = None,
    expense_growth: float | None = None,
    exit_cap_rate: float | None = None,
    interest_rate: float | None = None,
    loan_to_value: float | None = None,
    capital_expenditures: float = 0.0,
    assumptions: List[str] | None = None,
) -> Dict[str, Any]:
    """Independently simulate simplified CRE value/equity outcomes.

    All economic inputs are explicit. No perspective recommendation is accepted
    by this function, so agent conclusions cannot determine the distribution.
    Missing required inputs return an auditable insufficient-evidence result.
    """
    required = {"purchase_price": purchase_price, "noi": noi}
    missing = tuple(name for name, value in required.items() if value is None or value <= 0)
    if missing:
        return {
            "engine": "AletheiaTelos Independent CRE Monte Carlo Risk Engine v1",
            "independent_of_agents": True,
            "status": "INSUFFICIENT EVIDENCE",
            "missing_inputs": missing,
            "scenarios": [],
            "assumptions": assumptions or [],
        }

    occ = occupancy if occupancy is not None else 1.0
    growth = rent_growth if rent_growth is not None else 0.0
    exp_growth = expense_growth if expense_growth is not None else 0.0
    exit_cap = exit_cap_rate if exit_cap_rate is not None and exit_cap_rate > 0 else noi / purchase_price
    rate = interest_rate if interest_rate is not None else 0.0
    ltv = loan_to_value if loan_to_value is not None else 0.0
    debt = purchase_price * max(0.0, min(ltv, 0.99))
    equity_initial = purchase_price - debt
    rng = random.Random(seed)
    scenario_params = {
        "BASE": (growth, 0.02, occ, exit_cap),
        "BULL": (growth + 0.015, 0.01, min(1.0, occ + 0.03), max(0.0001, exit_cap - 0.005)),
        "BEAR": (growth - 0.02, 0.05, max(0.5, occ - 0.08), exit_cap + 0.01),
        "ADVERSARIAL": (growth - 0.04, 0.08, max(0.4, occ - 0.15), exit_cap + 0.02),
        "TAIL RISK": (growth - 0.07, 0.12, max(0.3, occ - 0.25), exit_cap + 0.04),
    }
    summaries: list[dict[str, Any]] = []
    for name, (growth_mu, growth_vol, occ_base, exit_cap_scenario) in scenario_params.items():
        equity_outcomes: list[float] = []
        drawdowns: list[float] = []
        for _ in range(paths):
            current_noi = float(noi)
            peak_equity = equity_initial
            worst_dd = 0.0
            for _year in range(max(1, hold_period)):
                annual_growth = rng.gauss(growth_mu, growth_vol)
                current_noi *= max(0.0, 1.0 + annual_growth)
                effective_noi = current_noi * occ_base
                current_noi = max(0.0, effective_noi * (1.0 - max(0.0, exp_growth)))
                debt_service = debt * rate if rate else 0.0
                annual_cash_flow = current_noi - debt_service - capital_expenditures
                equity_value = max(0.0, current_noi / exit_cap_scenario - debt)
                peak_equity = max(peak_equity, equity_value)
                if peak_equity:
                    worst_dd = max(worst_dd, (peak_equity - equity_value) / peak_equity)
            exit_value = max(0.0, current_noi / exit_cap_scenario)
            equity_outcomes.append(exit_value - debt + max(0.0, annual_cash_flow))
            drawdowns.append(worst_dd)
        summaries.append({
            "scenario": name,
            "mean_equity_outcome": round(mean(equity_outcomes), 2),
            "median_equity_outcome": round(median(equity_outcomes), 2),
            "p05_equity_outcome": round(_percentile(equity_outcomes, 0.05), 2),
            "p95_equity_outcome": round(_percentile(equity_outcomes, 0.95), 2),
            "probability_loss": round(sum(v < equity_initial for v in equity_outcomes) / paths, 4),
            "max_drawdown_mean": round(mean(drawdowns), 4),
        })
    return {
        "engine": "AletheiaTelos Independent CRE Monte Carlo Risk Engine v1",
        "independent_of_agents": True,
        "status": "SIMULATED",
        "paths": paths,
        "hold_period": hold_period,
        "seed": seed,
        "initial_equity": equity_initial,
        "scenarios": summaries,
        "assumptions": assumptions or [],
    }
