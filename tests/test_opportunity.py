from datetime import datetime, timezone

import pytest

from app.opportunity import (
    CREOpportunityDeal,
    CREOpportunityObservation,
    OpportunityProvenance,
    PropertyIdentityReference,
    build_cre_opportunity,
)


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def provenance(status="observed", source_refs=None):
    return OpportunityProvenance(
        source_refs=source_refs or ["E-1"],
        source_type="broker_listing",
        source_reference="SRC-1",
        observed_at=NOW,
        effective_at=NOW,
        status=status,
        uncertainty=["Requires independent verification."],
    )


def make_opportunity():
    observations = [
        CREOpportunityObservation(
            observation_id="OBS-ASK",
            category="deal_term",
            field_name="asking_price",
            value=12_000_000,
            status="sourced",
            provenance=provenance("sourced"),
            evidence_refs=["E-1"],
        ),
        CREOpportunityObservation(
            observation_id="OBS-NOI-A",
            category="operating",
            field_name="reported_noi",
            value=900_000,
            status="sourced",
            provenance=provenance("sourced", ["E-2"]),
            evidence_refs=["E-2"],
        ),
        CREOpportunityObservation(
            observation_id="OBS-NOI-B",
            category="operating",
            field_name="reported_noi",
            value=840_000,
            status="sourced",
            provenance=provenance("sourced", ["E-3"]),
            evidence_refs=["E-3"],
            uncertainty=["Conflicts with E-2."],
        ),
    ]
    return build_cre_opportunity(
        opportunity_id="OPP-1",
        property=PropertyIdentityReference(
            property_id="PROP-1",
            property_type="industrial",
            address="Example address",
            market="Vancouver, WA",
            units_or_sf=50_000,
            provenance=provenance("sourced"),
        ),
        source_type="broker_listing",
        source_reference="SRC-1",
        observed_at=NOW,
        effective_at=NOW,
        status="sourced",
        observations=observations,
        evidence_refs=["E-1", "E-2", "E-3"],
        source_refs=["E-1", "E-2", "E-3"],
        unknown_fields=["lease_expiration_dates", "tenant_credit_quality"],
        unresolved_fields=["normalized_noi"],
        conflict_refs=["CONFLICT-NOI-1"],
        uncertainty=["Reported NOI requires reconciliation."],
        created_at=NOW,
    )


def test_opportunity_is_typed_immutable_and_research_only():
    opportunity = make_opportunity()
    assert opportunity.opportunity_id == "OPP-1"
    assert opportunity.property.property_id == "PROP-1"
    assert opportunity.investment_authority == "none"
    assert opportunity.execution_capability is False
    assert opportunity.portfolio_mutation is False
    assert opportunity.authorization_capability is False
    with pytest.raises(Exception):
        opportunity.status = "superseded"


def test_opportunity_preserves_epistemic_status_and_provenance():
    opportunity = make_opportunity()
    asking = opportunity.observations[0]
    assert asking.status == "sourced"
    assert asking.value == 12_000_000
    assert asking.evidence_refs == ["E-1"]
    assert asking.provenance.status == "sourced"
    assert asking.provenance.source_reference == "SRC-1"


def test_incomplete_opportunity_remains_explicitly_incomplete():
    opportunity = build_cre_opportunity(
        opportunity_id="OPP-INCOMPLETE",
        property=PropertyIdentityReference(property_id="PROP-2"),
        status="unresolved",
        unknown_fields=["asking_price", "occupancy", "tenant_information"],
        unresolved_fields=["purchase_terms"],
        created_at=NOW,
    )
    assert opportunity.property.address is None
    assert "asking_price" in opportunity.unknown_fields
    assert "purchase_terms" in opportunity.unresolved_fields
    assert opportunity.observations == []


def test_conflicting_observations_can_coexist_without_overwrite():
    opportunity = make_opportunity()
    noi = [item for item in opportunity.observations if item.field_name == "reported_noi"]
    assert [item.value for item in noi] == [900_000, 840_000]
    assert opportunity.conflict_refs == ["CONFLICT-NOI-1"]
    assert opportunity.uncertainty == ["Reported NOI requires reconciliation."]


def test_new_opportunity_version_references_history_without_mutation():
    original = make_opportunity()
    revised = build_cre_opportunity(
        opportunity_id="OPP-2",
        property=original.property,
        status="sourced",
        observations=original.observations,
        evidence_refs=original.evidence_refs,
        source_refs=original.source_refs + ["E-4"],
        supersedes_opportunity_id=original.opportunity_id,
        created_at=datetime(2026, 9, 12, 15, 0, tzinfo=timezone.utc),
    )
    assert original.opportunity_id == "OPP-1"
    assert revised.opportunity_id == "OPP-2"
    assert revised.supersedes_opportunity_id == "OPP-1"
    assert original.source_refs == ["E-1", "E-2", "E-3"]


def test_invalid_identity_is_rejected():
    with pytest.raises(ValueError):
        PropertyIdentityReference(property_id="")
    with pytest.raises(ValueError):
        PropertyIdentityReference(property_id="PROP-X", units_or_sf=-1)


def test_serialization_is_valid_and_stable_for_same_artifact():
    opportunity = make_opportunity()
    first = opportunity.model_dump_json()
    second = opportunity.model_dump_json()
    assert first == second
    assert '"opportunity_id":"OPP-1"' in first
    assert '"investment_authority":"none"' in first
