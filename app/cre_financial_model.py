"""Pure CRE financial calculations used by the underwriting boundary.

This module contains no market-data retrieval, agent logic, authorization, or
execution. Every calculation is deterministic from explicit numeric inputs.
"""
from __future__ import annotations

import math
from typing import Sequence


def debt_service(principal: float, annual_rate: float, amortization_years: int | None, interest_only: bool = False) -> float | None:
    if principal < 0 or annual_rate < 0:
        return None
    if principal == 0:
        return 0.0
    if interest_only:
        return principal * annual_rate
    if amortization_years is None or amortization_years <= 0:
        return None
    if annual_rate == 0:
        return principal / amortization_years
    monthly_rate = annual_rate / 12
    periods = amortization_years * 12
    payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -periods)
    return payment * 12


def remaining_balance(principal: float, annual_rate: float, amortization_years: int | None, years_elapsed: int, interest_only: bool = False) -> float | None:
    if principal < 0 or annual_rate < 0 or years_elapsed < 0:
        return None
    if principal == 0:
        return 0.0
    if interest_only or amortization_years is None or amortization_years <= 0:
        return principal
    if annual_rate == 0:
        return max(0.0, principal * (1 - years_elapsed / amortization_years))
    monthly_rate = annual_rate / 12
    periods = amortization_years * 12
    k = min(periods, years_elapsed * 12)
    payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -periods)
    return max(0.0, principal * (1 + monthly_rate) ** k - payment * ((1 + monthly_rate) ** k - 1) / monthly_rate)


def irr(cash_flows: Sequence[float]) -> float | None:
    if not cash_flows or not (any(v > 0 for v in cash_flows) and any(v < 0 for v in cash_flows)):
        return None

    def npv(rate: float) -> float:
        return sum(value / ((1 + rate) ** period) for period, value in enumerate(cash_flows))

    low, high = -0.9999, 10.0
    low_value = npv(low)
    high_value = npv(high)
    if low_value * high_value > 0:
        return None
    for _ in range(120):
        mid = (low + high) / 2
        value = npv(mid)
        if abs(value) < 1e-9:
            return mid
        if low_value * value <= 0:
            high = mid
        else:
            low = mid
            low_value = value
    return (low + high) / 2


def effective_income(gross_rent: float | None, occupancy: float | None, vacancy: float | None, other_income: float | None = None) -> float | None:
    if gross_rent is None:
        return None
    if occupancy is not None and not 0 <= occupancy <= 1:
        return None
    if vacancy is not None and not 0 <= vacancy <= 1:
        return None
    vacancy_rate = vacancy if vacancy is not None else (1 - occupancy if occupancy is not None else None)
    if vacancy_rate is None:
        return None
    return gross_rent * max(0.0, 1 - vacancy_rate) + (other_income or 0.0)


def noi_from_operations(gross_rent: float | None, occupancy: float | None, vacancy: float | None, operating_expenses: float | None, other_income: float | None = None) -> float | None:
    income = effective_income(gross_rent, occupancy, vacancy, other_income)
    if income is None or operating_expenses is None or operating_expenses < 0:
        return None
    return income - operating_expenses


def break_even_occupancy(gross_rent: float, operating_expenses: float, debt_service_amount: float = 0.0, capital_expenditures: float = 0.0, other_income: float = 0.0) -> float | None:
    if gross_rent <= 0:
        return None
    return (operating_expenses + debt_service_amount + capital_expenditures - other_income) / gross_rent


def break_even_exit_cap(terminal_noi: float, net_sale_target: float, selling_cost_rate: float = 0.0) -> float | None:
    if terminal_noi <= 0 or net_sale_target <= 0 or not 0 <= selling_cost_rate < 1:
        return None
    return terminal_noi * (1 - selling_cost_rate) / net_sale_target


def max_purchase_price_for_cap(noi: float, target_cap_rate: float) -> float | None:
    if noi < 0 or target_cap_rate <= 0:
        return None
    return noi / target_cap_rate


def max_loan_for_dscr(noi: float, minimum_dscr: float, annual_rate: float, amortization_years: int | None, interest_only: bool = False) -> float | None:
    if noi < 0 or minimum_dscr <= 0 or annual_rate < 0:
        return None
    if annual_rate == 0 and not interest_only:
        return None
    per_dollar_service = debt_service(1.0, annual_rate, amortization_years, interest_only)
    if per_dollar_service is None or per_dollar_service <= 0:
        return None
    return noi / minimum_dscr / per_dollar_service
