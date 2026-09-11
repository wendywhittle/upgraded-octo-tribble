from app.simulator import run_cre_monte_carlo


BASE = dict(
    purchase_price=10_000_000,
    noi=700_000,
    hold_period=5,
    occupancy=0.95,
    rent_growth=0.03,
    expense_growth=0.02,
    exit_cap_rate=0.07,
    loan_to_value=0.65,
    interest_rate=0.06,
    amortization_years=25,
    capital_expenditures=25_000,
    selling_cost_rate=0.02,
)


def test_missing_occupancy_stays_unknown():
    result = run_cre_monte_carlo(**{**BASE, "occupancy": None}, paths=10)
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert "occupancy" in result["missing_inputs"]


def test_missing_rent_growth_stays_unknown():
    result = run_cre_monte_carlo(**{**BASE, "rent_growth": None}, paths=10)
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert "rent_growth" in result["missing_inputs"]


def test_missing_expense_growth_stays_unknown():
    result = run_cre_monte_carlo(**{**BASE, "expense_growth": None}, paths=10)
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert "expense_growth" in result["missing_inputs"]


def test_missing_ltv_does_not_become_zero_leverage():
    result = run_cre_monte_carlo(**{**BASE, "loan_to_value": None}, paths=10)
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert "loan_to_value" in result["missing_inputs"]


def test_explicit_zero_ltv_is_known_zero_leverage():
    result = run_cre_monte_carlo(**{**BASE, "loan_to_value": 0.0, "interest_rate": None, "amortization_years": None}, paths=10)
    assert result["status"] == "SIMULATED"
    assert result["loan_amount"] == 0.0
