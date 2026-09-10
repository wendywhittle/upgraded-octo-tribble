"""Independent Monte Carlo risk engine.

Agent conclusions provide assumptions to inspect, never simulation results. The
CRE engine below uses explicit property economics and reproducible scenario paths.
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


def run_monte_carlo(initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, assumptions: List[str] | None = None) -> Dict[str, Any]:
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


def _annual_debt_service(loan: float, rate: float, amortization_years: int | None) -> tuple[float, str]:
    if loan <= 0 or rate < 0:
        return 0.0, "none"
    if amortization_years is None or amortization_years <= 0:
        return loan * rate, "interest_only"
    if rate == 0:
        return loan / amortization_years, "amortizing"
    monthly_rate = rate / 12
    payment = loan * monthly_rate / (1 - (1 + monthly_rate) ** (-(amortization_years * 12)))
    return payment * 12, "amortizing"


def _remaining_balance(loan: float, rate: float, amortization_years: int | None, years: int) -> float:
    if loan <= 0:
        return 0.0
    if amortization_years is None or amortization_years <= 0 or rate == 0:
        if amortization_years and amortization_years > 0 and rate == 0:
            return max(0.0, loan * (1 - years / amortization_years))
        return loan
    monthly_rate = rate / 12
    n = amortization_years * 12
    k = min(n, years * 12)
    payment = loan * monthly_rate / (1 - (1 + monthly_rate) ** -n)
    return max(0.0, loan * (1 + monthly_rate) ** k - payment * ((1 + monthly_rate) ** k - 1) / monthly_rate)


def _irr(cash_flows: List[float]) -> float | None:
    if not cash_flows or not (any(v > 0 for v in cash_flows) and any(v < 0 for v in cash_flows)):
        return None
    low, high = -0.9999, 10.0
    def npv(rate: float) -> float:
        return sum(value / ((1 + rate) ** period) for period, value in enumerate(cash_flows))
    if npv(low) * npv(high) > 0:
        return None
    for _ in range(100):
        mid = (low + high) / 2
        value = npv(mid)
        if abs(value) < 1e-8:
            return mid
        if npv(low) * value <= 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def _cre_path(
    purchase_price: float,
    noi: float,
    hold_period: int,
    rng: random.Random,
    growth_mu: float,
    growth_vol: float,
    occupancy: float,
    exit_cap_rate: float,
    debt: float,
    debt_service: float,
    amortization_years: int | None,
    interest_rate: float,
    capital_expenditures: float,
    gross_rent: float | None,
    operating_expenses: float | None,
    expense_growth: float,
    vacancy: float | None,
    shock: float,
) -> dict[str, Any]:
    current_noi = float(noi)
    equity_initial = purchase_price - debt
    cash_flows: list[float] = []
    equity_values: list[float] = [equity_initial]
    for year in range(1, hold_period + 1):
        growth = rng.gauss(growth_mu, growth_vol)
        if gross_rent is not None and operating_expenses is not None:
            rent = gross_rent * (1 + growth_mu) ** year * max(0.0, 1 + rng.gauss(0.0, growth_vol))
            effective_occupancy = max(0.0, min(1.0, occupancy + rng.gauss(0.0, growth_vol)))
            vacancy_rate = vacancy if vacancy is not None else 1 - effective_occupancy
            income = rent * max(0.0, 1 - vacancy_rate)
            expenses = operating_expenses * (1 + expense_growth) ** year
            current_noi = max(0.0, income - expenses)
        else:
            current_noi = max(0.0, current_noi * (1 + growth) * max(0.0, min(1.0, occupancy)))
        if shock and year == max(1, hold_period // 2):
            current_noi *= max(0.0, 1 + shock)
        annual_cf = current_noi - debt_service - capital_expenditures
        cash_flows.append(annual_cf)
        remaining_debt = _remaining_balance(debt, interest_rate, amortization_years, year)
        equity_values.append(max(0.0, current_noi / exit_cap_rate - remaining_debt))
    exit_value = current_noi / exit_cap_rate
    remaining_debt = _remaining_balance(debt, interest_rate, amortization_years, hold_period)
    net_sale = exit_value - remaining_debt
    total_distributions = sum(cash_flows) + net_sale
    equity_multiple = total_distributions / equity_initial if equity_initial > 0 else None
    irr = _irr([-equity_initial, *cash_flows[:-1], cash_flows[-1] + net_sale]) if equity_initial > 0 else None
    return {
        "exit_value": exit_value,
        "net_sale_proceeds": net_sale,
        "equity_outcome": total_distributions,
        "equity_multiple": equity_multiple,
        "irr": irr,
        "cash_on_cash": cash_flows[0] / equity_initial if equity_initial > 0 else None,
        "dscr": noi / debt_service if debt_service > 0 else None,
        "debt_yield": noi / debt if debt > 0 else None,
        "equity_values": equity_values,
        "cash_flows": cash_flows,
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
    gross_rent: float | None = None,
    operating_expenses: float | None = None,
    vacancy: float | None = None,
    amortization_years: int | None = None,
    selling_cost_rate: float = 0.0,
) -> Dict[str, Any]:
    """Simulate simplified but explicit CRE cash-flow and equity outcomes."""
    required = {"purchase_price": purchase_price, "noi": noi, "hold_period": hold_period, "exit_cap_rate": exit_cap_rate}
    missing = tuple(name for name, value in required.items() if value is None or (isinstance(value, (int, float)) and value <= 0))
    if missing:
        return {
            "engine": "AletheiaTelos Independent CRE Monte Carlo Risk Engine v1",
            "independent_of_agents": True,
            "status": "INSUFFICIENT EVIDENCE",
            "missing_inputs": missing,
            "scenarios": [],
            "assumptions": assumptions or [],
        }
    if not 1 <= hold_period <= 100 or paths < 1:
        raise ValueError("hold_period must be 1..100 and paths must be positive")
    if occupancy is not None and not 0 <= occupancy <= 1:
        raise ValueError("occupancy must be between 0 and 1")
    if vacancy is not None and not 0 <= vacancy <= 1:
        raise ValueError("vacancy must be between 0 and 1")

    price = float(purchase_price)
    base_noi = float(noi)
    occ = occupancy if occupancy is not None else 1.0
    growth = rent_growth if rent_growth is not None else 0.0
    exp_growth = expense_growth if expense_growth is not None else 0.0
    exit_cap = float(exit_cap_rate)
    ltv = max(0.0, min(float(loan_to_value or 0.0), 0.99))
    debt = price * ltv
    rate = float(interest_rate or 0.0)
    debt_service, debt_method = _annual_debt_service(debt, rate, amortization_years)
    equity_initial = price - debt
    scenario_params = {
        "BASE": (growth, 0.02, occ, exit_cap, 0.0),
        "BULL": (growth + 0.015, 0.01, min(1.0, occ + 0.03), max(0.0001, exit_cap - 0.005), 0.0),
        "BEAR": (growth - 0.02, 0.05, max(0.5, occ - 0.08), exit_cap + 0.01, 0.0),
        "ADVERSARIAL": (growth - 0.04, 0.08, max(0.4, occ - 0.15), exit_cap + 0.02, -0.10),
        "TAIL RISK": (growth - 0.07, 0.12, max(0.3, occ - 0.25), exit_cap + 0.04, -0.25),
    }
    summaries: list[dict[str, Any]] = []
    for name, (growth_mu, growth_vol, occ_scenario, exit_cap_scenario, shock) in scenario_params.items():
        rng = random.Random(seed + sum(ord(c) for c in name))
        outcomes: list[float] = []
        exit_values: list[float] = []
        dscrs: list[float] = []
        cash_on_cash: list[float] = []
        equity_multiples: list[float] = []
        irrs: list[float] = []
        drawdowns: list[float] = []
        for _ in range(paths):
            path = _cre_path(price, base_noi, hold_period, rng, growth_mu, growth_vol, occ_scenario, exit_cap_scenario, debt, debt_service, amortization_years, rate, capital_expenditures, gross_rent, operating_expenses, exp_growth, vacancy, shock)
            outcome = path["equity_outcome"]
            outcomes.append(outcome)
            exit_values.append(path["exit_value"])
            if path["dscr"] is not None:
                dscrs.append(path["dscr"])
            if path["cash_on_cash"] is not None:
                cash_on_cash.append(path["cash_on_cash"])
            if path["equity_multiple"] is not None:
                equity_multiples.append(path["equity_multiple"])
            if path["irr"] is not None:
                irrs.append(path["irr"])
            drawdowns.append(_drawdown(path["equity_values"]))
        loss_base = equity_initial
        summaries.append({
            "scenario": name,
            "mean_equity_outcome": round(mean(outcomes), 2),
            "median_equity_outcome": round(median(outcomes), 2),
            "p05_equity_outcome": round(_percentile(outcomes, 0.05), 2),
            "p95_equity_outcome": round(_percentile(outcomes, 0.95), 2),
            "probability_loss": round(sum(v < loss_base for v in outcomes) / paths, 4) if loss_base > 0 else None,
            "max_drawdown_mean": round(mean(drawdowns), 4),
            "mean_exit_value": round(mean(exit_values), 2),
            "mean_dscr": round(mean(dscrs), 4) if dscrs else None,
            "mean_cash_on_cash": round(mean(cash_on_cash), 4) if cash_on_cash else None,
            "mean_equity_multiple": round(mean(equity_multiples), 4) if equity_multiples else None,
            "mean_irr": round(mean(irrs), 4) if irrs else None,
            "scenario_assumptions": {
                "rent_growth": growth_mu,
                "occupancy": occ_scenario,
                "exit_cap_rate": exit_cap_scenario,
                "shock": shock,
            },
        })
    return {
        "engine": "AletheiaTelos Independent CRE Monte Carlo Risk Engine v2",
        "independent_of_agents": True,
        "status": "SIMULATED",
        "paths": paths,
        "hold_period": hold_period,
        "seed": seed,
        "initial_equity": equity_initial,
        "loan_amount": debt,
        "annual_debt_service": debt_service,
        "debt_service_method": debt_method,
        "inputs": {
            "purchase_price": price,
            "noi": base_noi,
            "occupancy": occupancy,
            "gross_rent": gross_rent,
            "operating_expenses": operating_expenses,
            "rent_growth": rent_growth,
            "expense_growth": expense_growth,
            "interest_rate": interest_rate,
            "loan_to_value": loan_to_value,
            "amortization_years": amortization_years,
            "exit_cap_rate": exit_cap_rate,
            "selling_cost_rate": selling_cost_rate,
            "capital_expenditures": capital_expenditures,
        },
        "scenarios": summaries,
        "assumptions": assumptions or [],
    }


def cre_sensitivity(
    purchase_price: float,
    noi: float,
    hold_period: int = 5,
    occupancy: float | None = None,
    rent_growth: float | None = None,
    interest_rate: float | None = None,
    loan_to_value: float | None = None,
    exit_cap_rate: float | None = None,
    paths: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Small one-variable sensitivity table for identifying what breaks the deal."""
    base = run_cre_monte_carlo(purchase_price, noi, hold_period, paths, seed, occupancy, rent_growth, 0.0, exit_cap_rate or noi / purchase_price, interest_rate, loan_to_value)
    cases = {
        "rent_growth": [(-0.02, "-2.0%"), (0.0, "0.0%"), (0.02, "+2.0%")],
        "occupancy": [(0.75, "75%"), (0.90, "90%"), (0.98, "98%")],
        "interest_rate": [(0.05, "5.0%"), (0.07, "7.0%"), (0.09, "9.0%")],
        "exit_cap_rate": [(0.055, "5.5%"), (0.065, "6.5%"), (0.075, "7.5%")],
    }
    results: dict[str, Any] = {"base": base, "variables": {}}
    for variable, values in cases.items():
        rows = []
        for value, label in values:
            kwargs = {
                "occupancy": occupancy,
                "rent_growth": rent_growth,
                "interest_rate": interest_rate,
                "loan_to_value": loan_to_value,
                "exit_cap_rate": exit_cap_rate or noi / purchase_price,
            }
            kwargs[variable] = value
            sim = run_cre_monte_carlo(purchase_price, noi, hold_period, paths, seed, **kwargs)
            base_case = next((s for s in sim.get("scenarios", []) if s["scenario"] == "BASE"), None)
            rows.append({"value": label, "base_scenario": base_case})
        results["variables"][variable] = rows
    return results
