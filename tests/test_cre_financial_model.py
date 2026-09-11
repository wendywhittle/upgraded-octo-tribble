import pytest

from app.cre_underwriting import CREFinancialInputs, InputStatus, Assumption, underwrite_financial_model
from app.cre_decision import CREDecisionCriteria, evaluate_financial_decision
from app.cre_perspectives import assess_cre_opportunity
from app.cre_context import CREOpportunityContext
from app.cre_adversarial import review_cre_simulation
from app.conflict_intelligence import detect_cre_conflicts
from app.simulator import cre_sensitivity, run_cre_monte_carlo


def model_inputs(**overrides):
    values = dict(purchase_price=10_000_000, noi=700_000, occupancy=.95, rent_growth=.03, expense_growth=.02, loan_to_value=.65, interest_rate=.06, amortization_years=25, hold_period_years=5, exit_cap_rate=.07, selling_cost_rate=.02, capital_expenditures=25_000, closing_costs=0.0, evidence_ids=("ev-price", "ev-noi"))
    values.update(overrides)
    return CREFinancialInputs(**values)


def test_core_cre_returns_are_calculated_from_explicit_inputs():
    result = underwrite_financial_model(model_inputs())
    assert result.status == "CALCULATED"
    assert result.going_in_cap_rate == pytest.approx(.07)
    assert result.annual_debt_service is not None and result.dscr is not None
    assert result.debt_yield == pytest.approx(700_000 / 6_500_000)
    assert result.cash_on_cash is not None and result.exit_value is not None
    assert result.net_sale_proceeds is not None and result.equity_multiple is not None and result.irr is not None
    assert len(result.projected_noi) == 5 and len(result.projected_cash_flow) == 5


def test_amortizing_balance_reduces_and_interest_only_does_not():
    amortized = underwrite_financial_model(model_inputs()); io = underwrite_financial_model(model_inputs(interest_only=True))
    assert amortized.annual_equity_values[-1] != io.annual_equity_values[-1]
    assert io.annual_debt_service == pytest.approx(6_500_000 * .06)


def test_missing_exit_assumption_is_unknown_not_fabricated():
    result = underwrite_financial_model(model_inputs(exit_cap_rate=None))
    assert result.status == "INSUFFICIENT EVIDENCE" and "exit_cap_rate" in result.missing_inputs
    assert result.input_status["exit_cap_rate"] is InputStatus.UNKNOWN


def test_missing_closing_costs_is_unknown_not_fabricated():
    result = underwrite_financial_model(model_inputs(closing_costs=None))
    assert result.status == "INSUFFICIENT EVIDENCE" and "closing_costs" in result.missing_inputs
    assert result.input_status["closing_costs"] is InputStatus.UNKNOWN


def test_observed_and_assumed_inputs_remain_distinguishable():
    result = underwrite_financial_model(model_inputs())
    assert result.input_status["purchase_price"] is InputStatus.OBSERVED
    assert result.input_status["noi"] is InputStatus.OBSERVED
    assert result.input_status["rent_growth"] is InputStatus.ASSUMED
    assert result.input_status["exit_cap_rate"] is InputStatus.ASSUMED


def test_break_even_and_configured_thresholds_are_explicit():
    result = underwrite_financial_model(model_inputs(assumptions=(Assumption("target_cap_rate", .075, "ratio"), Assumption("minimum_dscr", 1.25, "x"))))
    assert result.break_even_occupancy is None
    assert result.break_even_exit_cap is not None
    assert result.max_purchase_price_at_target_cap == pytest.approx(700_000 / .075)
    assert result.max_loan_at_target_dscr is not None


def test_operating_ledger_projects_noi_from_explicit_rent_and_expenses():
    result = underwrite_financial_model(model_inputs(gross_rent=1_000_000, operating_expenses=200_000, occupancy=.95, other_income=10_000))
    assert result.projected_noi[0] == pytest.approx(1_000_000 * 1.03 * .95 + 10_000 - 200_000 * 1.02)


def test_explicit_criteria_can_produce_no_deal_without_authority():
    result = underwrite_financial_model(model_inputs(loan_to_value=.80, interest_rate=.09))
    decision = evaluate_financial_decision(result, CREDecisionCriteria(min_dscr=1.20, max_ltv=.75, min_irr=.12), supplied_ltv=.80)
    assert decision.state.value == "NO DEAL" and decision.human_decision_required is True and decision.autonomous_execution is False


def test_cre_simulation_uses_economic_outputs_not_price_paths():
    result = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=200, seed=11, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=.06, loan_to_value=.65, exit_cap_rate=.07, capital_expenditures=25_000, selling_cost_rate=.02, closing_costs=0.0, amortization_years=25)
    base = next(item for item in result["scenarios"] if item["scenario"] == "BASE")
    assert base["mean_exit_value"] != 100.0 and base["mean_dscr"] is not None and base["mean_equity_multiple"] is not None and base["mean_irr"] is not None


def test_scenarios_have_different_economic_assumptions():
    result = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=100, seed=11, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=.06, loan_to_value=.65, exit_cap_rate=.07, amortization_years=25, capital_expenditures=25_000, selling_cost_rate=.02, closing_costs=0.0)
    scenarios = {s["scenario"]: s for s in result["scenarios"]}
    assert scenarios["BASE"]["scenario_assumptions"] != scenarios["BEAR"]["scenario_assumptions"]
    assert scenarios["ADVERSARIAL"]["scenario_assumptions"]["exit_cap_rate"] > scenarios["BASE"]["scenario_assumptions"]["exit_cap_rate"]


def test_financing_unknown_prevents_simulation_from_inventing_rate():
    result = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=10, occupancy=.95, rent_growth=.03, expense_growth=.02, loan_to_value=.65, exit_cap_rate=.07, capital_expenditures=25_000, selling_cost_rate=.02, closing_costs=0.0)
    assert result["status"] == "INSUFFICIENT EVIDENCE" and "interest_rate" in result["missing_inputs"]


def test_sensitivity_changes_the_requested_variable():
    result = cre_sensitivity(10_000_000, 700_000, hold_period=5, paths=100, seed=3, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=None, loan_to_value=0.0, exit_cap_rate=.07, capital_expenditures=25_000)
    outcomes = [row["base_scenario"]["mean_equity_outcome"] for row in result["variables"]["exit_cap_rate"]]
    assert outcomes[0] > outcomes[-1]


def test_perspectives_share_the_same_economic_metrics():
    ctx = CREOpportunityContext("opp", "prop", "industrial", "Vancouver, WA", purchase_price=10_000_000, noi=700_000, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=.06, hold_period=5, exit_assumptions={"exit_cap_rate":.07}, financing_assumptions={"loan_to_value":.65, "amortization_years":25}, evidence=("ev-price", "ev-noi"))
    assessments = assess_cre_opportunity(ctx, underwrite_financial_model(model_inputs()))
    assert len(assessments) == 8 and len({a.perspective_id for a in assessments}) == 8
    assert all(a.economic_metrics["going_in_cap_rate"] == pytest.approx(.07) for a in assessments)
    assert all(a.economic_claims for a in assessments)


def test_conflict_preserves_economic_interpretations_without_averaging():
    ctx = CREOpportunityContext("opp", "prop", "industrial", "Vancouver, WA", purchase_price=10_000_000, noi=700_000, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=.06, hold_period=5, exit_assumptions={"exit_cap_rate":.07}, financing_assumptions={"loan_to_value":.65, "amortization_years":25}, evidence=("ev-price", "ev-noi"))
    assessments = assess_cre_opportunity(ctx, underwrite_financial_model(model_inputs()))
    conflicts = detect_cre_conflicts(assessments)
    assert conflicts
    assert any(item["dimension"] == "assumptions" or item["dimension"] == "downside" for item in conflicts)
    assert all(item["status"] == "unresolved" for item in conflicts)


def test_adversarial_review_references_actual_financial_outputs():
    model = underwrite_financial_model(model_inputs())
    sim = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=100, seed=7, occupancy=.95, rent_growth=.03, expense_growth=.02, interest_rate=.06, loan_to_value=.65, exit_cap_rate=.07, amortization_years=25, capital_expenditures=25_000, selling_cost_rate=.02, closing_costs=0.0)
    review = review_cre_simulation(sim, ("rent_growth=.03",), ("ev-price",), model)
    assert any("break-even occupancy" in item for item in review.challenges)
    assert any("Worst modeled scenario" in item for item in review.challenges)
