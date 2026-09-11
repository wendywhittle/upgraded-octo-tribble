from datetime import date, datetime, timezone

import pytest

from app.underwriting import (
    AcquisitionTerms,
    CREUnderwritingProForma,
    OperatingAssumptions,
    PropertyIdentity,
    ReturnOutputs,
    UnderwritingFinancingReference,
    UnderwritingProvenance,
    ValuationAssumptions,
    build_cre_underwriting,
)


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def provenance(status="assumed"):
    return UnderwritingProvenance(
        source_refs=["E-1"],
        source_date=date(2026, 9, 10),
        effective_at=NOW,
        status=status,
        uncertainty=["Input requires verification."],
    )


def make_underwriting():
    return build_cre_underwriting(
        underwriting_id="UW-1",
        property=PropertyIdentity(
            property_id="PROP-1",
            property_type="industrial",
            market="Vancouver, WA",
            units_or_sf=50000,
            identity_provenance=provenance("sourced"),
        ),
        acquisition=AcquisitionTerms(
            purchase_price=10_000_000,
            acquisition_costs=250_000,
            provenance=provenance("sourced"),
        ),
        operations=OperatingAssumptions(
            gross_revenue=900_000,
            vacancy_rate=0.05,
            operating_expenses=200_000,
            capex=50_000,
            revenue_growth_rate=0.03,
            expense_growth_rate=0.03,
            provenance=provenance(),
        ),
        valuation=ValuationAssumptions(
            exit_cap_rate=0.065,
            discount_rate=0.09,
            valuation_method="income",
            provenance=provenance(),
        ),
        financing=UnderwritingFinancingReference(
            capital_stack_id="CS-1",
            lender_evidence_ids=["LE-1", "LE-2"],
        ),
        returns=ReturnOutputs(
            equity_multiple=1.8,
            irr=0.14,
            provenance=provenance("calculated"),
        ),
        assumptions=["Revenue growth remains within the modeled range."],
        source_refs=["E-1"],
        uncertainty=["Exit cap rate is assumption-sensitive."],
        status="projected",
        created_at=NOW,
    )


def test_underwriting_is_typed_immutable_and_research_only():
    uw = make_underwriting()
    assert uw.property.property_id == "PROP-1"
    assert uw.acquisition.purchase_price == 10_000_000
    assert uw.status == "projected"
    assert uw.investment_authority == "none"
    assert uw.execution_capability is False
    assert uw.portfolio_mutation is False
    with pytest.raises(Exception):
        uw.acquisition = uw.acquisition


def test_underwriting_preserves_epistemic_distinctions_and_provenance():
    uw = make_underwriting()
    assert uw.operations.provenance.status == "assumed"
    assert uw.acquisition.provenance.status == "sourced"
    assert uw.returns.provenance.status == "calculated"
    assert uw.source_refs == ["E-1"]
    assert "Exit cap rate" in uw.uncertainty[0]


def test_invalid_financial_inputs_are_rejected():
    with pytest.raises(ValueError):
        AcquisitionTerms(purchase_price=0, provenance=provenance())
    with pytest.raises(ValueError):
        OperatingAssumptions(vacancy_rate=1.1, provenance=provenance())
    with pytest.raises(ValueError):
        ValuationAssumptions(exit_cap_rate=0, provenance=provenance())


def test_observed_artifact_cannot_smuggle_model_assumptions_as_facts():
    with pytest.raises(ValueError):
        CREUnderwritingProForma(
            underwriting_id="UW-OBS",
            created_at=NOW,
            property=PropertyIdentity(property_id="PROP-OBS"),
            acquisition=AcquisitionTerms(purchase_price=1_000_000, provenance=provenance("observed")),
            operations=OperatingAssumptions(provenance=provenance("observed")),
            valuation=ValuationAssumptions(provenance=provenance("observed")),
            assumptions=["Future rent increases."],
            status="observed",
        )


def test_financing_references_are_references_not_commitments():
    uw = make_underwriting()
    assert uw.financing.capital_stack_id == "CS-1"
    assert uw.financing.lender_evidence_ids == ["LE-1", "LE-2"]
    assert uw.investment_authority == "none"
