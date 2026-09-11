import pytest

from app.underwriting_calculations import (
    annual_debt_service,
    cap_rate,
    cash_flow_after_debt_service,
    cash_on_cash,
    dscr,
    effective_gross_income,
    implied_value,
    loan_amount,
    ltv,
    net_operating_income,
)


def test_operating_calculations_are_deterministic_and_traceable():
    egi = effective_gross_income(1_000_000, 50_000, input_refs=("evidence:rent", "assumption:vacancy"))
    noi = net_operating_income(egi.value, 300_000, input_refs=("assumption:opex",))
    assert egi.value == 950_000
    assert noi.value == 650_000
    assert egi.input_refs == ("evidence:rent", "assumption:vacancy")
    assert noi.formula_version == "cre-underwriting-v1"
    assert noi.authorization == "none"


def test_valuation_and_financing_calculations():
    assert cap_rate(650_000, 10_000_000).value == pytest.approx(0.065)
    assert implied_value(650_000, 0.065).value == pytest.approx(10_000_000)
    assert loan_amount(10_000_000, 0.70).value == pytest.approx(7_000_000)
    assert ltv(7_000_000, 10_000_000).value == pytest.approx(0.70)


def test_debt_service_zero_interest_is_supported():
    result = annual_debt_service(1_200_000, 0.0, 30)
    assert result.value == pytest.approx(40_000)


def test_debt_service_and_coverage():
    debt = annual_debt_service(7_000_000, 0.06, 30)
    coverage = dscr(650_000, debt.value)
    cash_flow = cash_flow_after_debt_service(650_000, debt.value)
    assert debt.value == pytest.approx(503_361.97, rel=1e-5)
    assert coverage.value == pytest.approx(650_000 / debt.value)
    assert cash_flow.value == pytest.approx(650_000 - debt.value)


def test_cash_on_cash():
    result = cash_on_cash(146_638.03, 3_000_000)
    assert result.value == pytest.approx(0.0488793433)


def test_zero_denominators_are_explicitly_unresolved():
    cap = cap_rate(100, 0)
    value = implied_value(100, 0)
    coverage = dscr(100, 0)
    leverage = ltv(100, 0)
    coc = cash_on_cash(100, 0)
    for result, missing in (
        (cap, "property_value"),
        (value, "cap_rate"),
        (coverage, "annual_debt_service"),
        (leverage, "property_value"),
        (coc, "equity_invested"),
    ):
        assert result.status == "unresolved"
        assert result.value is None
        assert result.missing_inputs == (missing,)


def test_negative_cash_flow_remains_a_calculated_value():
    result = cash_flow_after_debt_service(100, 125)
    assert result.status == "calculated"
    assert result.value == -25


def test_invalid_financing_inputs_are_rejected():
    with pytest.raises(ValueError):
        loan_amount(1_000_000, 1.1)
    with pytest.raises(ValueError):
        annual_debt_service(-1, 0.05, 30)
    with pytest.raises(ValueError):
        annual_debt_service(1_000, -0.01, 30)
    with pytest.raises(ValueError):
        annual_debt_service(1_000, 0.05, 0)


def test_non_finite_values_are_rejected():
    with pytest.raises(ValueError):
        effective_gross_income(float("inf"), 0)


def test_calculation_result_is_immutable_and_serializable():
    result = cap_rate(500_000, 10_000_000, input_refs=("underwriting:1",))
    with pytest.raises((TypeError, ValueError)):
        result.value = 0.1
    assert result.model_dump(mode="json") == result.model_dump(mode="json")


def test_calculations_do_not_contain_recommendation_or_authorization_fields():
    result = noi = net_operating_income(900, 300)
    dumped = result.model_dump()
    assert "recommendation" not in dumped
    assert dumped["authorization"] == "none"
