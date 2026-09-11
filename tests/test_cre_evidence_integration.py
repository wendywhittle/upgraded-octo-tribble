from datetime import datetime, timezone

from app.cre_evidence import CREEvidenceProvenance, build_cre_evidence
from app.investment_case import build_structured_investment_case
from app.opportunity import PropertyIdentityReference, build_cre_opportunity


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def test_opportunity_and_investment_case_can_carry_typed_cre_evidence():
    evidence = build_cre_evidence(
        evidence_id="CRE-E1",
        opportunity_id="OPP-1",
        category="listing",
        field_name="asking_price",
        observed_value=4_500_000,
        observation_type="source_observation",
        status="sourced",
        provenance=CREEvidenceProvenance(
            source="broker",
            source_type="listing",
            source_reference="SRC-1",
            observed_at=NOW,
            retrieved_at=NOW,
            point_in_time=True,
        ),
        created_at=NOW,
    )
    opportunity = build_cre_opportunity(
        opportunity_id="OPP-1",
        property=PropertyIdentityReference(property_id="PROP-1"),
        evidence_refs=[evidence.evidence_id],
        created_at=NOW,
    )
    case = build_structured_investment_case(
        question="Evaluate opportunity",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={},
        opportunity_deal=opportunity,
        cre_evidence=[evidence],
        created_at=NOW,
    )
    assert opportunity.evidence_refs == ["CRE-E1"]
    assert case.cre_evidence[0].opportunity_id == opportunity.opportunity_id
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False
