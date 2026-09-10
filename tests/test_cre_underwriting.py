import pytest

from app.cre_underwriting import (
    Assumption,
    Property,
    UnderwritingDecision,
    UnderwritingInputs,
    underwrite,
)


def inputs(**overrides):
    values = dict(
        opportunity_id="deal-001",
        property=Property("prop-001", "industrial", "Vancouver, WA", 50000, 0.95, 2005),
        purchase_price=10_000_000,
        annual_noi=650_000,
        assumptions=(),
        evidence_ids=("ev-1",),
    )
    values.update(overrides)
    return UnderwritingInputs(**values)


def test_underwriting_calculates_cap_rate_without_authorizing():
    result = underwrite(inputs())
    assert result.going_in_cap_rate == pytest.approx(0.065)
    assert result.decision is UnderwritingDecision.WATCH


def test_missing_price_is_insufficient_evidence():
    result = underwrite(inputs(purchase_price=None))
    assert result.decision is UnderwritingDecision.INSUFFICIENT_EVIDENCE
    assert "purchase_price" in result.missing_inputs
    assert result.going_in_cap_rate is None


def test_missing_noi_is_not_fabricated():
    result = underwrite(inputs(annual_noi=None))
    assert result.decision is UnderwritingDecision.INSUFFICIENT_EVIDENCE
    assert "annual_noi" in result.missing_inputs


def test_low_confidence_assumption_and_invalidation_are_visible():
    assumption = Assumption(
        name="renewal_rent_growth",
        value=0.02,
        unit="annual_rate",
        source="management_estimate",
        evidence_id="ev-2",
        confidence=0.4,
        invalidation_condition="Market rents decline for two consecutive periods",
    )
    result = underwrite(inputs(assumptions=(assumption,)))
    assert "renewal_rent_growth" in result.fragile_assumptions
    assert result.invalidation_conditions == (
        "Market rents decline for two consecutive periods",
    )


def test_contradictory_evidence_is_preserved():
    result = underwrite(
        inputs(contradictory_evidence=("ev-contradictory-1",), uncertainty_notes=("Tenant renewal is uncertain",))
    )
    assert "Contradictory evidence" in result.reasons[1]
    assert "Material uncertainty" in result.reasons[2]


def test_no_deal_is_explicit_and_requires_a_reason():
    result = underwrite(inputs(no_deal_reasons=("Downside risk is unacceptable.",)))
    assert result.decision is UnderwritingDecision.NO_DEAL
    assert "Downside risk is unacceptable." in result.reasons


def test_invalid_assumption_confidence_is_rejected():
    with pytest.raises(ValueError):
        Assumption("bad", 1, "x", confidence=1.1)
