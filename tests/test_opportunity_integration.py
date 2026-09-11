from datetime import datetime, timezone

from app.investment_case import build_structured_investment_case
from app.opportunity import PropertyIdentityReference, build_cre_opportunity
from app.underwriting import (
    AcquisitionTerms,
    OperatingAssumptions,
    PropertyIdentity,
    UnderwritingProvenance,
    ValuationAssumptions,
    build_cre_underwriting,
)


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def provenance(status="assumed"):
    return UnderwritingProvenance(status=status, source_refs=["E-1"])


def make_opportunity():
    return build_cre_opportunity(
        opportunity_id="OPP-INT-1",
        property=PropertyIdentityReference(
            property_id="PROP-INT-1",
            property_type="industrial",
            market="Vancouver, WA",
        ),
        status="sourced",
        evidence_refs=["E-1"],
        created_at=NOW,
    )


def make_underwriting(opportunity_id=None):
    return build_cre_underwriting(
        underwriting_id="UW-INT-1",
        opportunity_id=opportunity_id,
        property=PropertyIdentity(property_id="PROP-INT-1"),
        acquisition=AcquisitionTerms(purchase_price=1_000_000, provenance=provenance("sourced")),
        operations=OperatingAssumptions(provenance=provenance()),
        valuation=ValuationAssumptions(provenance=provenance()),
        created_at=NOW,
    )


def test_underwriting_can_reference_opportunity_without_embedding_or_authorizing_it():
    opportunity = make_opportunity()
    underwriting = make_underwriting(opportunity.opportunity_id)
    assert underwriting.opportunity_id == opportunity.opportunity_id
    assert underwriting.investment_authority == "none"
    assert underwriting.execution_capability is False
    assert underwriting.portfolio_mutation is False


def test_structured_investment_case_can_carry_opportunity_without_authority():
    opportunity = make_opportunity()
    case = build_structured_investment_case(
        question="Should this CRE opportunity be investigated?",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={"verdict": "NO_DATA"},
        opportunity_deal=opportunity,
        created_at=NOW,
    )
    assert case.opportunity_deal is opportunity
    assert case.opportunity_deal.opportunity_id == "OPP-INT-1"
    assert case.recommendation == "NO_DATA"
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False
    assert not any("canonical CRE opportunity" in gap for gap in case.gaps)
