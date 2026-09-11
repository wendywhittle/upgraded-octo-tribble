from copy import deepcopy

import pytest

from app.capital_stack import (
    CapitalSource,
    CapitalStack,
    CapitalStackValidationError,
    CapitalUse,
    DebtTerms,
    analyze_capital_stack,
    validate_financing_provenance,
)
from app.proforma import ProFormaInput, calculate_proforma


def make_proforma():
    return calculate_proforma(ProFormaInput(
        asset_id="asset-1",
        acquisition_price=10_000_000,
        acquisition_costs=500_000,
        projection_years=5,
        annual_rent=900_000,
        initial_occupancy=1.0,
        rent_growth=0.03,
        vacancy_rate=0.0,
        operating_expenses=250_000,
        entry_cap_rate=0.065,
        exit_cap_rate=0.07,
    ))


def make_stack(debt=6_000_000, equity=4_500_000):
    return CapitalStack(
        sources=[
            CapitalSource(
                name="Senior Loan",
                source_type="SENIOR_DEBT",
                amount=debt,
                provenance="SOURCE",
                debt_terms=DebtTerms(interest_rate=0.06, amortization_years=30, maturity_years=5),
            ),
            CapitalSource(
                name="Sponsor Equity",
                source_type="SPONSOR_EQUITY",
                amount=equity,
                provenance="ASSUMPTION",
            ),
        ],
        uses=[
            CapitalUse(name="Acquisition", use_type="ACQUISITION_PRICE", amount=10_000_000),
            CapitalUse(name="Closing Costs", use_type="ACQUISITION_COSTS", amount=500_000),
        ],
    )


def test_sources_and_uses_balance_and_totals_are_deterministic():
    stack = make_stack()
    assert stack.total_sources == 10_500_000
    assert stack.total_uses == 10_500_000
    assert stack.variance == 0
    assert stack.balanced is True
    assert stack.model_copy(deep=True).total_sources == stack.total_sources


def test_unbalanced_sources_and_uses_are_explicit():
    stack = make_stack(equity=4_000_000)
    assert stack.total_sources == 10_000_000
    assert stack.total_uses == 10_500_000
    assert stack.variance == -500_000
    assert stack.balanced is False
    with pytest.raises(CapitalStackValidationError, match="do not reconcile"):
        analyze_capital_stack(stack, proforma=make_proforma())


def test_negative_source_and_use_amounts_rejected():
    with pytest.raises(ValueError):
        CapitalSource(name="Bad", source_type="EQUITY", amount=-1)
    with pytest.raises(ValueError):
        CapitalUse(name="Bad", use_type="OTHER", amount=-1)


def test_debt_terms_are_required_only_for_debt_sources():
    with pytest.raises(ValueError, match="require debt_terms"):
        CapitalSource(name="Senior", source_type="SENIOR_DEBT", amount=1_000_000)
    with pytest.raises(ValueError, match="only be supplied"):
        CapitalSource(
            name="Equity", source_type="COMMON_EQUITY", amount=1_000_000,
            debt_terms=DebtTerms(interest_rate=0.05, amortization_years=30, maturity_years=5),
        )


def test_invalid_debt_terms_rejected():
    with pytest.raises(ValueError):
        DebtTerms(interest_rate=-0.01, amortization_years=30, maturity_years=5)
    with pytest.raises(ValueError):
        DebtTerms(interest_rate=0.06, amortization_years=0, maturity_years=5)
    with pytest.raises(ValueError):
        DebtTerms(interest_rate=0.06, amortization_years=30, maturity_years=0)


def test_financing_metrics_are_deterministic_and_calculated():
    proforma = make_proforma()
    result = analyze_capital_stack(make_stack(), proforma=proforma)

    assert result.asset_id == "asset-1"
    assert result.total_debt == 6_000_000
    assert result.equity_requirement == 4_500_000
    assert result.loan_to_value == pytest.approx(6_000_000 / proforma.entry_valuation)
    assert result.loan_to_cost == pytest.approx(6_000_000 / 10_500_000)
    assert result.annual_debt_service > 0
    assert result.debt_service_coverage_ratio == pytest.approx(
        proforma.annual[0].noi / result.annual_debt_service
    )
    assert result.debt_yield == pytest.approx(proforma.annual[0].noi / 6_000_000)
    assert all(value == "CALCULATION" for value in result.output_types.values())
    assert result.provenance["financing_metrics"] == "CALCULATION"


def test_principal_reduction_and_balloon_balance_are_exposed():
    result = analyze_capital_stack(make_stack(), proforma=make_proforma())
    debt = result.debt_analyses[0]

    assert len(debt.annual_principal_reduction) == 5
    assert all(value >= 0 for value in debt.annual_principal_reduction)
    assert debt.balloon_balance > 0
    assert debt.output_types["balloon_balance"] == "CALCULATION"


def test_zero_rate_debt_is_supported_deterministically():
    stack = CapitalStack(
        sources=[
            CapitalSource(
                name="Zero Rate Loan", source_type="SENIOR_DEBT", amount=1_000_000,
                debt_terms=DebtTerms(interest_rate=0, amortization_years=10, maturity_years=5),
            ),
            CapitalSource(name="Equity", source_type="COMMON_EQUITY", amount=9_500_000),
        ],
        uses=[
            CapitalUse(name="Acquisition", use_type="ACQUISITION_PRICE", amount=10_000_000),
            CapitalUse(name="Costs", use_type="ACQUISITION_COSTS", amount=500_000),
        ],
    )
    result = analyze_capital_stack(stack, proforma=make_proforma())
    assert result.annual_debt_service == 100_000
    assert result.debt_analyses[0].balloon_balance == 500_000


def test_proforma_is_consumed_without_mutation_or_recalculation():
    proforma = make_proforma()
    before = deepcopy(proforma.model_dump(mode="json"))
    result = analyze_capital_stack(make_stack(), proforma=proforma)
    after = proforma.model_dump(mode="json")

    assert before == after
    assert result.debt_service_coverage_ratio == pytest.approx(
        proforma.annual[0].noi / result.annual_debt_service
    )


def test_leveraged_cash_flow_is_derived_from_authoritative_property_cash_flow():
    proforma = make_proforma()
    result = analyze_capital_stack(make_stack(), proforma=proforma)
    expected = [round(cf - result.annual_debt_service, 2) for cf in proforma.unlevered_cash_flows[1:]]
    assert result.leveraged_cash_flows == expected


def test_property_value_can_be_supplied_without_changing_proforma():
    proforma = make_proforma()
    result = analyze_capital_stack(make_stack(), proforma=proforma, property_value=12_000_000)
    assert result.property_value == 12_000_000
    assert result.loan_to_value == pytest.approx(0.5)
    assert result.asset_id == proforma.asset_id


def test_agent_supplied_financing_metrics_cannot_become_authoritative():
    with pytest.raises(CapitalStackValidationError, match="cannot be supplied"):
        validate_financing_provenance([{"agent_id": "quant", "dscr": 2.0}])
    with pytest.raises(CapitalStackValidationError, match="cannot be supplied"):
        validate_financing_provenance([{"ltv": 0.60, "debt_yield": 0.08}])


def test_financing_analysis_has_no_authorization_or_execution_surface():
    result = analyze_capital_stack(make_stack(), proforma=make_proforma())
    assert not hasattr(result, "authorize")
    assert not hasattr(result, "deploy_capital")
    assert not hasattr(result, "execute_transaction")
    assert not hasattr(result, "create_portfolio_position")
    assert result.provenance["authority"] == "CAPITAL_STACK_ANALYSIS_ONLY"


def test_identical_inputs_produce_identical_outputs():
    proforma = make_proforma()
    first = analyze_capital_stack(make_stack(), proforma=proforma).model_dump(mode="json")
    second = analyze_capital_stack(make_stack(), proforma=proforma).model_dump(mode="json")
    assert first == second
