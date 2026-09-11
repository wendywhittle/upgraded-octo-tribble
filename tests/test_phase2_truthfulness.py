from app.cre_decision import CREDecisionCriteria, evaluate_financial_decision
from app.cre_underwriting import CREFinancialInputs, InputStatus, underwrite_financial_model
from app.memory import build_record


def _financial():
    return underwrite_financial_model(CREFinancialInputs(
        purchase_price=10_000_000,
        noi=700_000,
        occupancy=.95,
        rent_growth=.03,
        expense_growth=.02,
        loan_to_value=.65,
        interest_rate=.06,
        amortization_years=25,
        hold_period_years=5,
        exit_cap_rate=.07,
        selling_cost_rate=.02,
        capital_expenditures=25_000,
        closing_costs=0.0,
        evidence_ids=("EV-PRICE", "EV-NOI", "EV-FINANCING"),
    ))


def test_unknown_ltv_is_insufficient_evidence_not_no_deal():
    decision = evaluate_financial_decision(_financial(), CREDecisionCriteria(max_ltv=.70), supplied_ltv=None)
    assert decision.state.value == "INSUFFICIENT EVIDENCE"
    assert not decision.criteria_failed
    assert decision.unresolved_questions


def test_memory_preserves_assumptions_and_explicit_decision_record():
    record = build_record(
        "Assess CRE opportunity",
        [{"agent_id": "quant", "evidence": ["EV-NOI"], "assumptions": ["rent_growth=.03"]}],
        {"conflicts": []},
        {"independent_of_agents": True, "scenarios": []},
        {"recommendation": "hold"},
        {"verdict": "INVESTIGATE"},
        {"human_decision_required": True, "autonomous_execution": False},
        42,
        decision={
            "state": "WATCH",
            "rationale": "Further diligence required.",
            "criteria_satisfied": (),
            "criteria_failed": (),
            "unresolved_questions": ("Verify lease terms",),
            "evidence_ids": ("EV-NOI",),
            "human_decision_required": True,
            "autonomous_execution": False,
        },
    )
    assert record["assumptions"] == ["rent_growth=.03"]
    assert record["decision"]["state"] == "WATCH"
    assert record["decision"]["human_decision_required"] is True
