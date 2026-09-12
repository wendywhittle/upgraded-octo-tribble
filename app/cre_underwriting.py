"""CRE underwriting engine for research-only real-asset investment analysis.

The engine computes transparent underwriting metrics from explicitly supplied inputs.
Missing inputs remain unknown rather than being inferred or fabricated. Results are
research outputs only and carry no investment or execution authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CREUnderwritingRequest:
    purchase_price: Optional[float] = None
    annual_effective_gross_income: Optional[float] = None
    annual_operating_expenses: Optional[float] = None
    closing_costs: float = 0.0
    capex: float = 0.0
    ltv: Optional[float] = None
    interest_rate: Optional[float] = None
    amortization_years: Optional[int] = None
    hold_years: Optional[int] = None
    annual_income_growth: float = 0.0
    annual_expense_growth: float = 0.0
    exit_cap_rate: Optional[float] = None
    selling_cost_rate: float = 0.0


def _valid(value: Optional[float]) -> bool:
    return value is not None and isfinite(float(value))


def _positive(value: Optional[float]) -> bool:
    return _valid(value) and float(value) > 0


def _annual_debt_service(principal: float, rate: float, years: int) -> float:
    monthly_rate = rate / 12.0
    periods = years * 12
    if monthly_rate == 0:
        return principal / years
    payment = principal * monthly_rate / (1.0 - (1.0 + monthly_rate) ** (-periods))
    return payment * 12.0


def _balance_after_years(principal: float, rate: float, amort_years: int, elapsed_years: int) -> float:
    monthly_rate = rate / 12.0
    n = amort_years * 12
    k = min(elapsed_years * 12, n)
    if monthly_rate == 0:
        return max(0.0, principal * (1.0 - k / n))
    payment = principal * monthly_rate / (1.0 - (1.0 + monthly_rate) ** (-n))
    return max(0.0, principal * (1.0 + monthly_rate) ** k - payment * ((1.0 + monthly_rate) ** k - 1.0) / monthly_rate)


def _irr(cash_flows: list[float]) -> Optional[float]:
    if not cash_flows or not any(x > 0 for x in cash_flows) or not any(x < 0 for x in cash_flows):
        return None
    low, high = -0.9999, 10.0
    def npv(rate: float) -> float:
        return sum(cf / ((1.0 + rate) ** year) for year, cf in enumerate(cash_flows))
    if npv(low) * npv(high) > 0:
        return None
    for _ in range(120):
        mid = (low + high) / 2
        value = npv(mid)
        if abs(value) < 1e-8:
            return mid
        if npv(low) * value <= 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def underwrite_cre(request: CREUnderwritingRequest) -> Dict[str, Any]:
    """Return transparent CRE metrics plus explicit unknowns and assumptions."""
    p = request.purchase_price
    income = request.annual_effective_gross_income
    expenses = request.annual_operating_expenses
    result: Dict[str, Any] = {
        "status": "INSUFFICIENT_INPUTS",
        "research_only": True,
        "investment_authority": False,
        "inputs": asdict(request),
        "metrics": {},
        "unknown_metrics": [],
        "assumptions": [],
    }

    if _valid(income) and _valid(expenses):
        noi = income - expenses
        result["metrics"]["noi"] = noi
    else:
        result["unknown_metrics"].append("noi")
        noi = None

    if _positive(p) and noi is not None:
        result["metrics"]["cap_rate"] = noi / p
    else:
        result["unknown_metrics"].append("cap_rate")

    loan = None
    equity = None
    if _positive(p) and _valid(request.ltv):
        loan = p * request.ltv
        equity = p + request.closing_costs + request.capex - loan
        result["metrics"]["loan_amount"] = loan
        result["metrics"]["initial_equity"] = equity
    else:
        result["unknown_metrics"].extend(["loan_amount", "initial_equity"])

    debt_service = None
    if loan is not None and _valid(request.interest_rate) and request.amortization_years and request.amortization_years > 0:
        debt_service = _annual_debt_service(loan, request.interest_rate, request.amortization_years)
        result["metrics"]["annual_debt_service"] = debt_service
        if noi is not None and debt_service > 0:
            result["metrics"]["dscr"] = noi / debt_service
        else:
            result["unknown_metrics"].append("dscr")
    else:
        result["unknown_metrics"].extend(["annual_debt_service", "dscr"])

    if noi is not None and debt_service is not None and equity is not None and equity > 0:
        result["metrics"]["annual_cash_flow"] = noi - debt_service
        result["metrics"]["cash_on_cash"] = (noi - debt_service) / equity
    else:
        result["unknown_metrics"].extend(["annual_cash_flow", "cash_on_cash"])

    hold = request.hold_years
    if hold and hold > 0 and noi is not None and _positive(request.exit_cap_rate) and _positive(p):
        cash_flows = []
        current_income = income
        current_expenses = expenses
        initial_equity = equity if equity is not None else p + request.closing_costs + request.capex
        cash_flows.append(-initial_equity)
        for year in range(1, hold + 1):
            current_income *= 1.0 + request.annual_income_growth
            current_expenses *= 1.0 + request.annual_expense_growth
            year_noi = current_income - current_expenses
            year_debt = debt_service or 0.0
            year_cash_flow = year_noi - year_debt
            if year == hold:
                exit_value = year_noi / request.exit_cap_rate
                selling_costs = exit_value * request.selling_cost_rate
                loan_balance = _balance_after_years(loan, request.interest_rate, request.amortization_years, hold) if loan is not None and _valid(request.interest_rate) and request.amortization_years else 0.0
                net_sale = exit_value - selling_costs - loan_balance
                year_cash_flow += net_sale
                result["metrics"].update({"exit_value": exit_value, "selling_costs": selling_costs, "loan_balance_at_exit": loan_balance, "net_sale_proceeds": net_sale})
            cash_flows.append(year_cash_flow)
        irr = _irr(cash_flows)
        result["metrics"]["irr"] = irr
        result["metrics"]["equity_multiple"] = (sum(cash_flows[1:]) / initial_equity) if initial_equity > 0 else None
    else:
        result["unknown_metrics"].extend(["exit_value", "irr", "equity_multiple"])

    result["unknown_metrics"] = sorted(set(result["unknown_metrics"]))
    result["status"] = "COMPLETE" if not result["unknown_metrics"] else "PARTIAL"
    result["assumptions"] = [
        "Only explicitly supplied property and financing inputs are used.",
        "NOI equals effective gross income minus operating expenses.",
        "Cap rate equals NOI divided by purchase price.",
        "Cash-on-cash uses annual pre-tax cash flow after modeled debt service divided by initial equity.",
        "Exit analysis uses forward NOI divided by exit cap rate and subtracts selling costs and modeled loan balance.",
    ]
    return result
