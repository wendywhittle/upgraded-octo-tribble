import pytest

from app.cre_decision import CREDecisionCriteria, evaluate_financial_decision
from app.cre_underwriting import CREFinancialInputs, UnderwritingDecision, underwrite_financial_model


BASE = dict(
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
    closing_costs=0.0,
    evidence_ids=("EV-PRICE", "EV-NOI", "EV-OCCUPANCY", "EV-LEASE", "EV-FINANCING"),
)


def model(**overrides):
    values = {**BASE, **overrides}
    return underwrite_financial_model(CREFinancialInputs(**values))


def test_cre_has_exactly_four_decision_states():
    assert {state.value for state in UnderwritingDecision} == {
        "ACT",
        "WATCH",
        "NO DEAL",
        "INSUFFICIENT EVIDENCE",
    }


def test_missing_ltv_is_unknown_in_financial_model():
    result = model(loan_to_value=None, loan_amount=None)
    assert result.status == "INSUFFICIENT EVIDENCE"
    assert "loan_to_value" in result.missing_inputs
    assert result.input_status["loan_to_value"].value == "UNKNOWN"


def test_missing_growth_inputs_are_unknown_not_zero_growth():
    rent = model(rent_growth=None)
    expense = model(expense_growth=None)
    assert rent.status == "INSUFFICIENT EVIDENCE"
    assert "rent_growth" in rent.missing_inputs
    assert expense.status == "INSUFFICIENT EVIDENCE"
    assert "expense_growth" in expense.missing_inputs


def test_missing_capex_and_selling_cost_are_unknown_not_zero():
    capex = model(capital_expenditures=None)
    selling = model(selling_cost_rate=None)
    assert capex.status == "INSUFFICIENT EVIDENCE"
    assert "capital_expenditures" in capex.missing_inputs
    assert selling.status == "INSUFFICIENT EVIDENCE"
    assert "selling_cost_rate" in selling.missing_inputs


def test_explicit_zero_values_remain_known():
    result = model(loan_to_value=0.0, capital_expenditures=0.0, selling_cost_rate=0.0, rent_growth=0.0, expense_growth=0.0, interest_rate=None, amortization_years=None)
    assert result.status == "CALCULATED"
    assert result.equity_requirement == pytest.approx(10_000_000)


def test_max_ltv_unknown_cannot_become_act():
    result = model(loan_to_value=None, loan_amount=None)
    decision = evaluate_financial_decision(result, CREDecisionCriteria(max_ltv=0.70), supplied_ltv=None)
    assert decision.state is UnderwritingDecision.INSUFFICIENT_EVIDENCE


def test_decision_record_exposes_criteria_and_human_authority():
    decision = evaluate_financial_decision(
        model(),
        CREDecisionCriteria(min_dscr=1.20, min_irr=0.12, max_ltv=0.70),
        supplied_ltv=0.65,
    )
    assert decision.state is UnderwritingDecision.ACT
    assert decision.criteria_satisfied
    assert decision.criteria_failed == ()
    assert decision.human_decision_required is True
    assert decision.autonomous_execution is False
