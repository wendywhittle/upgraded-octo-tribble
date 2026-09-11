import pytest

from app.cre_decision import CREDecisionCriteria, CREDecisionRecord, build_decision_record, evaluate_financial_decision
from app.cre_underwriting import CREFinancialInputs, UnderwritingDecision, UnderwritingResult, underwrite_financial_model


def result(state=UnderwritingDecision.NO_DEAL):
    return UnderwritingResult(state, None, reasons=("Margin of safety is insufficient.",), evidence_ids=("ev-1",))


def model(**overrides):
    values = dict(purchase_price=10_000_000, noi=700_000, occupancy=.95, rent_growth=.03, expense_growth=.02, loan_to_value=.65, interest_rate=.06, amortization_years=25, hold_period_years=5, exit_cap_rate=.07, selling_cost_rate=.02, capital_expenditures=25_000, closing_costs=0.0, evidence_ids=("ev-1",))
    values.update(overrides)
    return underwrite_financial_model(CREFinancialInputs(**values))


def test_decision_record_preserves_no_deal_and_requires_human():
    record = build_decision_record(result(), ("Verify tenant rollover",))
    assert record.state is UnderwritingDecision.NO_DEAL
    assert record.human_decision_required is True
    assert record.autonomous_execution is False
    assert record.unresolved_questions == ("Verify tenant rollover",)


def test_decision_record_cannot_disable_human_authority():
    with pytest.raises(ValueError):
        CREDecisionRecord(UnderwritingDecision.ACT, "x", human_decision_required=False)


def test_decision_record_cannot_enable_execution():
    with pytest.raises(ValueError):
        CREDecisionRecord(UnderwritingDecision.ACT, "x", autonomous_execution=True)


def test_configured_criteria_can_produce_act_recommendation_without_authority():
    record = evaluate_financial_decision(model(), CREDecisionCriteria(min_dscr=1.20, min_cash_on_cash=.04, min_irr=.12, min_equity_multiple=1.5, max_ltv=.70), supplied_ltv=.65)
    assert record.state is UnderwritingDecision.ACT
    assert record.human_decision_required is True
    assert record.autonomous_execution is False
    assert "human authorization" in record.rationale
