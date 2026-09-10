import pytest

from app.cre_underwriting import CREFinancialInputs, InputStatus, underwrite_financial_model
from app.cre_decision import CREDecisionCriteria, evaluate_financial_decision
from app.simulator import cre_sensitivity, run_cre_monte_carlo


def model_inputs(**overrides):
    values = dict(
        purchase_price=10_000_000,
        noi=700_000,
        occupancy=0.95,
        rent_growth=0.03,
        expense_growth=0.02,
        loan_to_value=0.65,
        interest_rate=0.06,
        amortization_years=25,
        hold_period_years=5,
        exit_cap_rate=0.07,
        selling_cost_rate=0.02,
        capital_expenditures=25_000,
        evidence_ids=("ev-price", "ev-noi"),
    )
    values.update(overrides)
    return CREFinancialInputs(**values)


def test_core_cre_returns_are_calculated_from_explicit_inputs():
    result = underwrite_financial_model(model_inputs())
    assert result.status == "CALCULATED"
    assert result.going_in_cap_rate == pytest.approx(0.07)
    assert result.annual_debt_service is not None
    assert result.dscr is not None
    assert result.debt_yield == pytest.approx(700_000 / 6_500_000)
    assert result.cash_on_cash is not None
    assert result.exit_value is not None
    assert result.net_sale_proceeds is not None
    assert result.equity_multiple is not None
    assert result.irr is not None
    assert len(result.projected_noi) == 5
    assert len(result.projected_cash_flow) == 5


def test_missing_exit_assumption_is_unknown_not_fabricated():
    result = underwrite_financial_model(model_inputs(exit_cap_rate=None))
    assert result.status == "INSUFFICIENT EVIDENCE"
    assert "exit_cap_rate" in result.missing_inputs
    assert result.input_status["exit_cap_rate"] is InputStatus.UNKNOWN


def test_observed_and_assumed_inputs_remain_distinguishable():
    result = underwrite_financial_model(model_inputs())
    assert result.input_status["purchase_price"] is InputStatus.OBSERVED
    assert result.input_status["noi"] is InputStatus.OBSERVED
    assert result.input_status["rent_growth"] is InputStatus.ASSUMED
    assert result.input_status["exit_cap_rate"] is InputStatus.ASSUMED


def test_explicit_criteria_can_produce_no_deal_without_authority():
    result = underwrite_financial_model(model_inputs(loan_to_value=0.80, interest_rate=0.09))
    decision = evaluate_financial_decision(
        result,
        CREDecisionCriteria(min_dscr=1.20, max_ltv=0.75, min_irr=0.12),
        supplied_ltv=0.80,
    )
    assert decision.state.value == "NO DEAL"
    assert decision.human_decision_required is True
    assert decision.autonomous_execution is False


def test_cre_simulation_uses_economic_outputs_not_price_paths():
    result = run_cre_monte_carlo(
        10_000_000, 700_000, hold_period=5, paths=200, seed=11,
        occupancy=0.95, rent_growth=0.03, interest_rate=0.06,
        loan_to_value=0.65, exit_cap_rate=0.07, capital_expenditures=25_000,
        amortization_years=25,
    )
    base = next(item for item in result["scenarios"] if item["scenario"] == "BASE")
    assert "mean_exit_value" in base
    assert "mean_dscr" in base
    assert "mean_equity_multiple" in base
    assert "mean_irr" in base
    assert base["mean_exit_value"] != 100.0


def test_sensitivity_changes_the_requested_variable():
    result = cre_sensitivity(10_000_000, 700_000, hold_period=5, paths=100, seed=3, occupancy=0.95, rent_growth=0.03, interest_rate=0.06, loan_to_value=0.65, exit_cap_rate=0.07)
    rows = result["variables"]["exit_cap_rate"]
    outcomes = [row["base_scenario"]["mean_equity_outcome"] for row in rows]
    assert outcomes[0] > outcomes[-1]
