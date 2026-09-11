"""Deterministic CRE underwriting calculations.

This module calculates explicit financial inputs without inventing assumptions,
authorizing investment, executing transactions, or mutating portfolio state.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

CalculationStatus = Literal["calculated", "unresolved"]


@dataclass(frozen=True)
class CalculationResult:
    """Immutable calculation output with its explicit inputs and provenance."""

    calculation_type: str
    status: CalculationStatus
    value: float | None
    input_values: tuple[tuple[str, float], ...]
    input_refs: tuple[str, ...] = ()
    formula_version: str = "cre-underwriting-v1"
    missing_inputs: tuple[str, ...] = ()
    error: str | None = None

    @property
    def authorization(self) -> Literal["none"]:
        return "none"


def _finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _result(
    calculation_type: str,
    value: float,
    inputs: dict[str, float],
    input_refs: tuple[str, ...],
) -> CalculationResult:
    _finite("calculated value", value)
    return CalculationResult(
        calculation_type=calculation_type,
        status="calculated",
        value=value,
        input_values=tuple(sorted(inputs.items())),
        input_refs=input_refs,
    )


def _unresolved(
    calculation_type: str,
    missing_inputs: tuple[str, ...],
    inputs: dict[str, float],
    input_refs: tuple[str, ...],
) -> CalculationResult:
    return CalculationResult(
        calculation_type=calculation_type,
        status="unresolved",
        value=None,
        input_values=tuple(sorted(inputs.items())),
        input_refs=input_refs,
        missing_inputs=missing_inputs,
    )


def effective_gross_income(
    gross_potential_income: float,
    vacancy_credit_loss: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    return _result(
        "effective_gross_income",
        gross_potential_income - vacancy_credit_loss,
        {"gross_potential_income": gross_potential_income, "vacancy_credit_loss": vacancy_credit_loss},
        input_refs,
    )


def net_operating_income(
    effective_gross_income_value: float,
    operating_expenses: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    return _result(
        "net_operating_income",
        effective_gross_income_value - operating_expenses,
        {"effective_gross_income": effective_gross_income_value, "operating_expenses": operating_expenses},
        input_refs,
    )


def cap_rate(
    noi: float,
    property_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if property_value == 0:
        return _unresolved("cap_rate", ("property_value",), {"noi": noi, "property_value": property_value}, input_refs)
    return _result("cap_rate", noi / property_value, {"noi": noi, "property_value": property_value}, input_refs)


def implied_value(
    noi: float,
    cap_rate_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if cap_rate_value == 0:
        return _unresolved("implied_value", ("cap_rate",), {"noi": noi, "cap_rate": cap_rate_value}, input_refs)
    return _result("implied_value", noi / cap_rate_value, {"noi": noi, "cap_rate": cap_rate_value}, input_refs)


def loan_amount(
    property_value: float,
    ltv_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if ltv_value < 0 or ltv_value > 1:
        raise ValueError("ltv must be between 0 and 1")
    return _result("loan_amount", property_value * ltv_value, {"property_value": property_value, "ltv": ltv_value}, input_refs)


def annual_debt_service(
    principal: float,
    annual_interest_rate: float,
    amortization_years: int,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if principal < 0:
        raise ValueError("principal cannot be negative")
    if annual_interest_rate < 0:
        raise ValueError("annual_interest_rate cannot be negative")
    if amortization_years <= 0:
        raise ValueError("amortization_years must be positive")

    periods = amortization_years * 12
    monthly_rate = annual_interest_rate / 12
    if monthly_rate == 0:
        monthly_payment = principal / periods
    else:
        monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-periods))
    return _result(
        "annual_debt_service",
        monthly_payment * 12,
        {"principal": principal, "annual_interest_rate": annual_interest_rate, "amortization_years": float(amortization_years)},
        input_refs,
    )


def dscr(
    noi: float,
    annual_debt_service_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if annual_debt_service_value == 0:
        return _unresolved("dscr", ("annual_debt_service",), {"noi": noi, "annual_debt_service": annual_debt_service_value}, input_refs)
    return _result("dscr", noi / annual_debt_service_value, {"noi": noi, "annual_debt_service": annual_debt_service_value}, input_refs)


def ltv(
    loan_value: float,
    property_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if property_value == 0:
        return _unresolved("ltv", ("property_value",), {"loan_amount": loan_value, "property_value": property_value}, input_refs)
    return _result("ltv", loan_value / property_value, {"loan_amount": loan_value, "property_value": property_value}, input_refs)


def cash_flow_after_debt_service(
    noi: float,
    annual_debt_service_value: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    return _result(
        "cash_flow_after_debt_service",
        noi - annual_debt_service_value,
        {"noi": noi, "annual_debt_service": annual_debt_service_value},
        input_refs,
    )


def cash_on_cash(
    annual_cash_flow: float,
    equity_invested: float,
    *,
    input_refs: tuple[str, ...] = (),
) -> CalculationResult:
    if equity_invested == 0:
        return _unresolved("cash_on_cash", ("equity_invested",), {"annual_cash_flow": annual_cash_flow, "equity_invested": equity_invested}, input_refs)
    return _result("cash_on_cash", annual_cash_flow / equity_invested, {"annual_cash_flow": annual_cash_flow, "equity_invested": equity_invested}, input_refs)
