from app.simulator import run_cre_monte_carlo


def test_missing_hold_period_does_not_default_to_five_years():
    result = run_cre_monte_carlo(
        10_000_000,
        700_000,
        occupancy=.95,
        rent_growth=.03,
        expense_growth=.02,
        exit_cap_rate=.07,
        loan_to_value=.65,
        interest_rate=.06,
        amortization_years=25,
        capital_expenditures=25_000,
        selling_cost_rate=.02,
        closing_costs=0.0,
    )
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert "hold_period" in result["missing_inputs"]
