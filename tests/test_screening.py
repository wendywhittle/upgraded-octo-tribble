from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.cre_evidence import CREEvidenceProvenance, build_cre_evidence
from app.opportunity import PropertyIdentityReference, build_cre_opportunity
from app.screening import (
    ScreeningCriterion,
    build_cre_opportunity_screening,
    validate_screening_scope,
)

NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def criterion(**overrides):
    value = {
        "criterion_id": "price-fit",
        "name": "Deal size fit",
        "status": "satisfied",
        "epistemic_status": "sourced",
        "value": 2500000,
        "evidence_refs": ["CRE-E1"],
        "rationale": "Reported asking price is within the screening range.",
        "critical": True,
    }
    value.update(overrides)
    return ScreeningCriterion(**value)


def screening(**overrides):
    value = {
        "screening_id": "SCREEN-1",
        "opportunity_id": "OPP-1",
        "created_at": NOW,
        "criteria": [criterion()],
        "disposition": "PASS",
        "positive_factors": ["Deal size fit"],
        "evidence_refs": ["CRE-E1"],
    }
    value.update(overrides)
    return build_cre_opportunity_screening(**value)


def opportunity():
    return build_cre_opportunity(
        opportunity_id="OPP-1",
        property=PropertyIdentityReference(property_id="PROP-1", property_type="industrial"),
        created_at=NOW,
    )


def cre_evidence():
    return build_cre_evidence(
        evidence_id="CRE-E1",
        opportunity_id="OPP-1",
        category="listing",
        field_name="asking_price",
        observed_value=2500000,
        source_content="Asking price reported as $2.5M.",
        observation_type="source_observation",
        status="sourced",
        provenance=CREEvidenceProvenance(
            source="verified-source",
            source_type="broker_listing",
            source_reference="SRC-1",
            observed_at=NOW,
            retrieved_at=NOW,
            point_in_time=True,
        ),
        created_at=NOW,
    )


def test_valid_construction_and_dispositions():
    assert screening().disposition == "PASS"
    for disposition in ("FAIL", "HOLD", "INSUFFICIENT_DATA"):
        assert screening(screening_id=f"S-{disposition}", disposition=disposition).disposition == disposition


def test_invalid_identity_and_disposition_rejected():
    with pytest.raises(ValidationError):
        screening(screening_id="")
    with pytest.raises(ValidationError):
        screening(opportunity_id="")
    with pytest.raises(ValidationError):
        screening(disposition="MAYBE")


def test_malformed_criterion_rejected():
    with pytest.raises(ValidationError):
        criterion(criterion_id="")
    with pytest.raises(ValidationError):
        criterion(status="unknown")


def test_evidence_sufficiency_states_are_explicit():
    assert screening(disposition="INSUFFICIENT_DATA", missing_critical_evidence=["rent_roll"]).disposition == "INSUFFICIENT_DATA"
    assert screening(
        disposition="FAIL",
        negative_factors=["Asset type outside mandate"],
    ).disposition == "FAIL"
    assert screening(
        disposition="HOLD",
        unresolved_factors=["Conflicting occupancy evidence"],
        risk_flags=["Occupancy conflict"],
    ).disposition == "HOLD"
    assert screening(disposition="PASS").disposition == "PASS"


def test_unknown_is_not_failure():
    item = screening(
        disposition="INSUFFICIENT_DATA",
        criteria=[criterion(status="missing_evidence", epistemic_status="unresolved", value=None)],
        missing_critical_evidence=["lease_term"],
    )
    assert item.disposition == "INSUFFICIENT_DATA"
    assert item.criteria[0].value is None
    assert item.criteria[0].epistemic_status == "unresolved"


def test_conflicting_evidence_remains_referenceable():
    item = screening(
        disposition="HOLD",
        criteria=[criterion(status="conflicting_evidence", rationale="Two occupancy sources disagree.")],
        unresolved_factors=["Occupancy requires resolution"],
    )
    assert item.criteria[0].status == "conflicting_evidence"
    assert item.evidence_refs == ["CRE-E1"]


def test_history_does_not_mutate_prior_screening():
    old = screening(screening_id="SCREEN-OLD", disposition="HOLD")
    new = screening(
        screening_id="SCREEN-NEW",
        disposition="PASS",
        supersedes_screening_id=old.screening_id,
    )
    assert old.disposition == "HOLD"
    assert new.supersedes_screening_id == old.screening_id


def test_screening_is_immutable_and_non_authoritative():
    item = screening()
    with pytest.raises(ValidationError):
        item.disposition = "FAIL"
    assert item.investment_authority == "none"
    assert item.execution_capability is False
    assert item.portfolio_mutation is False
    assert item.transaction_capability is False
    assert item.authorization_capability is False


def test_screening_does_not_create_assumption_or_recommendation_fields():
    item = screening()
    payload = item.model_dump()
    assert "assumption" not in payload
    assert "recommendation" not in payload
    assert "authorization" not in payload


def test_serialization_is_deterministic():
    item = screening()
    assert item.model_dump(mode="json") == item.model_dump(mode="json")
    assert item.model_dump(mode="json")["opportunity_id"] == "OPP-1"


def test_scope_matches_opportunity_and_evidence():
    validate_screening_scope(screening(), opportunity(), [cre_evidence()])


def test_scope_rejects_wrong_opportunity_or_unknown_evidence():
    with pytest.raises(ValueError):
        validate_screening_scope(screening(opportunity_id="OPP-2"), opportunity(), [cre_evidence()])
    with pytest.raises(ValueError):
        validate_screening_scope(screening(evidence_refs=["CRE-UNKNOWN"]), opportunity(), [cre_evidence()])
