from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.cre_evidence import CREEvidenceProvenance, build_cre_evidence, validate_cre_evidence
from app.evidence import validate_evidence

NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def provenance(**overrides):
    value = {
        "source": "verified-source",
        "source_type": "broker_listing",
        "source_reference": "SRC-1",
        "publisher": "Example Broker",
        "observed_at": NOW - timedelta(minutes=10),
        "effective_at": NOW - timedelta(minutes=10),
        "retrieved_at": NOW - timedelta(minutes=5),
        "point_in_time": True,
    }
    value.update(overrides)
    return CREEvidenceProvenance(**value)


def evidence(**overrides):
    value = {
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
    value.update(overrides)
    return build_cre_evidence(**value)


def test_construction_and_opportunity_link():
    item = evidence()
    assert item.evidence_id == "CRE-E1"
    assert item.opportunity_id == "OPP-1"
    assert item.investment_authority == "none"


def test_invalid_identity_rejected():
    with pytest.raises(ValidationError):
        evidence(evidence_id="")
    with pytest.raises(ValidationError):
        evidence(opportunity_id="")


def test_temporal_order_rejected():
    with pytest.raises(ValidationError):
        evidence(provenance=provenance(retrieved_at=NOW - timedelta(hours=1)))


def test_provenance_and_epistemic_status_preserved():
    item = evidence()
    assert item.provenance.source == "verified-source"
    assert item.provenance.source_reference == "SRC-1"
    assert item.provenance.observed_at == NOW - timedelta(minutes=10)
    assert item.status == "sourced"


def test_evidence_is_immutable_and_research_only():
    item = evidence()
    with pytest.raises(ValidationError):
        item.observed_value = 0.91
    assert item.execution_capability is False
    assert item.portfolio_mutation is False
    assert item.transaction_capability is False


def test_conflicting_evidence_coexists():
    first = evidence(evidence_id="CRE-E-A", observed_value=0.98)
    second = evidence(
        evidence_id="CRE-E-B",
        observed_value=0.91,
        contradictory_evidence_refs=[first.evidence_id],
        conflict_refs=["CONFLICT-1"],
    )
    assert first.observed_value == 0.98
    assert second.observed_value == 0.91
    assert second.contradictory_evidence_refs == ["CRE-E-A"]


def test_supersession_preserves_history():
    old = evidence(evidence_id="CRE-E-OLD", observed_value=0.94)
    new = evidence(
        evidence_id="CRE-E-NEW",
        observed_value=0.91,
        status="superseded",
        supersedes_evidence_id=old.evidence_id,
    )
    assert old.observed_value == 0.94
    assert new.supersedes_evidence_id == old.evidence_id


def test_generic_validation_is_reused():
    assert validate_cre_evidence(evidence(), now=NOW)["decision_usable"] is True
    blocked = validate_cre_evidence(
        evidence(provenance=provenance(source_type="synthetic_demo")), now=NOW
    )
    assert blocked["decision_usable"] is False


def test_existing_generic_evidence_remains_compatible():
    generic = {
        "evidence_id": "E1",
        "source": "verified-source",
        "claim": "Observed claim",
        "observed_at": (NOW - timedelta(minutes=5)).isoformat(),
        "retrieved_at": (NOW - timedelta(minutes=2)).isoformat(),
        "provenance": {"type": "external_source", "point_in_time": True},
    }
    assert validate_evidence(generic, now=NOW)["decision_usable"] is True


def test_unknown_value_remains_unknown():
    item = evidence(observed_value=None, status="unresolved", uncertainty=["Not supplied by source."])
    assert item.observed_value is None
    assert item.status == "unresolved"


def test_serialization_is_stable():
    item = evidence()
    assert item.model_dump(mode="json") == item.model_dump(mode="json")
    assert item.model_dump(mode="json")["opportunity_id"] == "OPP-1"
