from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.cre_evidence import (
    CREEvidence,
    CREEvidenceProvenance,
    build_cre_evidence,
    validate_cre_evidence,
)
from app.evidence import validate_evidence


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def provenance(**overrides):
    values = {
        "source": "verified-source",
        "source_type": "broker_listing",
        "source_reference": "SRC-1",
        "publisher": "Example Broker",
        "observed_at": NOW - timedelta(minutes=10),
        "effective_at": NOW - timedelta(minutes=10),
        "retrieved_at": NOW - timedelta(minutes=5),
        "point_in_time": True,
    }
    values.update(overrides)
    return CREEvidenceProvenance(**values)


def evidence(**overrides):
    values = {
        "evidence_id": "CRE-E1",
        "opportunity_id": "OPP-1",
        "category": "listing",
        "subject_ref": "PROP-1",
        "field_name": "occupancy",
        "observed_value": 0.94,
        "source_content": "Occupancy reported as 94%.",
        "observation_type": "source_observation",
        "status": "sourced",
        "provenance": provenance(),
        "created_at": NOW,
    }
    values.update(overrides)
    return build_cre_evidence(**values)


def test_valid_cre_evidence_construction_and_opportunity_association():
    item = evidence()
    assert item.evidence_id == "CRE-E1"
    assert item.opportunity_id == "OPP-1"
    assert item.observed_value == 0.94
    assert item.investment_authority == "none"


def test_invalid_identity_rejected():
    with pytest.raises(ValidationError):
        evidence(evidence_id="")
    with pytest.raises(ValidationError):
        evidence(opportunity_id="")


def test_invalid_temporal_order_rejected():
    with pytest.raises(ValidationError):
        evidence(provenance=provenance(retrieved_at=NOW - timedelta(hours=1)))


def test_provenance_is_preserved():
    item = evidence()
    assert item.provenance.source == "verified-source"
    assert item.provenance.source_reference == "SRC-1"
    assert item.provenance.observed_at == NOW - timedelta(minutes=10)
    assert item.provenance.retrieved_at == NOW - timedelta(minutes=5)
    assert item.provenance.effective_at == NOW - timedelta(minutes=10)


def test_evidence_does_not_have_downstream_epistemic_authority():
    item = evidence()
    assert item.status in {"observed", "sourced", "unresolved", "superseded"}
    assert item.investment_authority == "none"
    assert item.execution_capability is False
    assert item.portfolio_mutation is False
    assert item.transaction_capability is False
    assert not hasattr(item, "assumption")
    assert not hasattr(item, "recommendation")


def test_immutability_is_enforced():
    item = evidence()
    with pytest.raises(ValidationError):
        item.observed_value = 0.91


def test_conflicting_evidence_coexists_without_overwrite():
    a = evidence(evidence_id="CRE-E-A", observed_value=0.98)
    b = evidence(
        evidence_id="CRE-E-B",
        observed_value=0.91,
        contradictory_evidence_refs=[a.evidence_id],
        conflict_refs=["CONFLICT-1"],
    )
    assert a.observed_value == 0.98
    assert b.observed_value == 0.91
    assert b.contradictory_evidence_refs == ["CRE-E-A"]
    assert b.conflict_refs == ["CONFLICT-1"]


def test_historical_supersession_preserves_original():
    original = evidence(evidence_id="CRE-E-OLD", observed_value=0.94)
    updated = evidence(
        evidence_id="CRE-E-NEW",
        observed_value=0.91,
        status="superseded",
        supersedes_evidence_id=original.evidence_id,
    )
    assert original.observed_value == 0.94
    assert updated.supersedes_evidence_id == "CRE-E-OLD"


def test_generic_validation_remains_usable():
    result = validate_cre_evidence(evidence(), now=NOW)
    assert result["valid"] is True
    assert result["decision_usable"] is True


def test_generic_synthetic_demo_restriction_is_reused():
    item = evidence(provenance=provenance(source_type="synthetic_demo"))
    result = validate_cre_evidence(item, now=NOW)
    assert result["decision_usable"] is False
    assert any("Synthetic demo" in error for error in result["errors"])


def test_generic_evidence_behavior_is_unchanged():
    generic = {
        "evidence_id": "E1",
        "source": "verified-source",
        "claim": "Observed claim",
        "observed_at": (NOW - timedelta(minutes=5)).isoformat(),
        "retrieved_at": (NOW - timedelta(minutes=2)).isoformat(),
        "provenance": {"type": "external_source", "point_in_time": True},
    }
    assert validate_evidence(generic, now=NOW)["decision_usable"] is True


def test_stable_serialization():
    item = evidence()
    assert item.model_dump(mode="json") == item.model_dump(mode="json")
    assert item.model_dump(mode="json")["opportunity_id"] == "OPP-1"


def test_unknown_is_represented_by_missing_observation_not_invented_fact():
    item = evidence(observed_value=None, status="unresolved", uncertainty=["Not supplied by source."])
    assert item.observed_value is None
    assert item.status == "unresolved"
    assert item.uncertainty == ["Not supplied by source."]
