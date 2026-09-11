import pytest

from app.proforma import ProFormaInput, calculate_proforma
from app.workflow import InvestmentCase


def case(**overrides):
    values = dict(
        asset_id="TEST-CRE-001",
        acquisition_price=1_000_000,
        acquisition_costs=20_000,
        projection_years=3,
        annual_rent=100_000,
        other_income=0,
        initial_occupancy=0.95,
        vacancy_rate=0,
        rent_growth=0.02,
        operating_expenses=20_000,
        expense_growth=0.02,
        entry_cap_rate=0.08,
        exit_cap_rate=0.08,
        capex=5_000,
        reserves=2_000,
        exit_costs=10_000,
    )
    values.update(overrides)
    return ProFormaInput(**values)


def test_basic_proforma_calculates_revenue_noi_and_cash_flow():
    result = calculate_proforma(case())
    assert result.acquisition_basis == 1_020_000
    assert result.annual[0].effective_gross_income == 95_000
    assert result.annual[0].noi == 75_000
    assert result.annual[0].property_cash_flow == 68_000


def test_entry_and_exit_valuation_are_calculated():
    result = calculate_proforma(case())
    assert result.entry_valuation == 937_500
    assert result.exit_valuation > 0
    assert result.terminal_value == result.exit_valuation


def test_unlevered_cash_flow_and_returns_are_calculated():
    result = calculate_proforma(case())
    assert result.unlevered_cash_flows[0] == -1_020_000
    assert len(result.unlevered_cash_flows) == 4
    assert result.unlevered_irr is not None
    assert result.unlevered_equity_multiple > 0


def test_deterministic_reproducibility():
    inputs = case()
    assert calculate_proforma(inputs).model_dump() == calculate_proforma(inputs).model_dump()


@pytest.mark.parametrize(
    "field,value",
    [("acquisition_price", 0), ("initial_occupancy", 1.01), ("entry_cap_rate", 0), ("exit_cap_rate", 0)],
)
def test_invalid_inputs_are_rejected(field, value):
    with pytest.raises(ValueError):
        case(**{field: value})


def test_occupancy_and_vacancy_cannot_exceed_one():
    with pytest.raises(ValueError):
        case(initial_occupancy=0.8, vacancy_rate=0.3)


def test_agent_style_irr_input_is_not_part_of_authoritative_input_model():
    result = calculate_proforma(case())
    assert "irr" not in case().model_fields
    assert result.unlevered_irr is not None


def test_proforma_result_can_be_attached_to_versioned_investment_case():
    result = calculate_proforma(case())
    investment_case = InvestmentCase(deal_id="deal-1", version=1)
    investment_case.proforma = result.model_dump(mode="json")
    assert investment_case.proforma["engine"].startswith("AletheiaTelos Deterministic CRE")
