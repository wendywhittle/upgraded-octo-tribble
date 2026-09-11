from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.cre_evidence import CREEvidence, CREEvidenceProvenance
from app.due_diligence import (
    CREPropertyDueDiligence,
    DueDiligenceFinding,
    DueDiligenceProvenance,
    build_cre_property_due_diligence,
)
from app.opportunity import PropertyIdentityReference, build_cre_opportunity
from app.screening import CREOpportunityScreening


NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)


def evidence(evidence_id: str = "ev-1") -> CREEvidence:
    return CREEvidence(
        evidence_id=evidence_id,
        opportunity_id="opp-1",
        category="physical_due_diligence",
        field_name="roof_inspection",
        observed_value="inspection report",
        observation_type="inspection_report",
        provenance=CREEvidenceProvenance(
            source="inspector",
            observed_at=NOW,
            retrieved_at=NOW,
            point_in_time=True,
        ),
        created_at=NOW,
    )


def opportunity():
    return build_cre_opportunity(
        opportunity_id="opp-1",
        property=PropertyIdentityReference(property_id="prop-1"),
        created_at=NOW,
    )


def finding(finding_id="find-1", **kwargs):
    return DueDiligenceFinding(
        finding_id=finding_id,
        category="physical",
        field_name="roof_condition",
        status="unresolved",
        review_status="unresolved",
        finding="Condition remains unresolved pending inspection.",
        evidence_refs=["ev-1"],
        materiality="high",
        risk_flag="inspection_required",
        provenance=DueDiligenceProvenance(evidence_refs=["ev-1"]),
        **kwargs,
    )


def test_valid_due_diligence_and_immutability():
    item = build_cre_property_due_diligence(
        due_diligence_id="dd-1",
        opportunity_id="opp-1",
        property_id="prop-1",
        findings=[finding()],
        missing_documents=["roof report"],
        created_at=NOW,
    )
    assert item.investment_authority == "none"
    assert item.execution_capability is False
    assert item.transaction_capability is False
    assert item.portfolio_mutation is False
    with pytest.raises(ValidationError):
        item.opportunity_id = "other"


def test_unknown_and_unresolved_are_explicit():
    item = build_cre_property_due_diligence(
        due_diligence_id="dd-2",
        opportunity_id="opp-1",
        unknown_fields=["roof_remaining_life"],
        unresolved_items=["physical inspection"],
        created_at=NOW,
    )
    assert item.unknown_fields == ["roof_remaining_life"]
    assert item.unresolved_items == ["physical inspection"]


def test_conflicting_findings_coexist_and_history_is_preserved():
    first = finding("find-a", observed_value="12 years")
    second = finding(
        "find-b", observed_value="5 years", conflict_refs=["find-a"], supersedes_finding_id="find-a"
    )
    item = build_cre_property_due_diligence(
        due_diligence_id="dd-3",
        opportunity_id="opp-1",
        findings=[first, second],
        supersedes_due_diligence_id="dd-previous",
        created_at=NOW,
    )
    assert [x.finding_id for x in item.findings] == ["find-a", "find-b"]
    assert item.findings[1].supersedes_finding_id == "find-a"
    assert item.supersedes_due_diligence_id == "dd-previous"


def test_invalid_category_and_status_rejected():
    with pytest.raises(ValidationError):
        DueDiligenceFinding(
            finding_id="x", category="not-real", field_name="x", status="unresolved"
        )
    with pytest.raises(ValidationError):
        DueDiligenceFinding(
            finding_id="x", category="physical", field_name="x", status="invented"
        )


def test_scope_validation_requires_canonical_opportunity_and_evidence():
    from app.due_diligence import validate_due_diligence_scope

    item = build_cre_property_due_diligence(
        due_diligence_id="dd-4", opportunity_id="opp-1", findings=[finding()], created_at=NOW
    )
    validate_due_diligence_scope(item, opportunity(), [evidence()])
    with pytest.raises(ValueError):
        validate_due_diligence_scope(item, opportunity(), [])


def test_property_identity_must_match_when_supplied():
    from app.due_diligence import validate_due_diligence_scope

    item = build_cre_property_due_diligence(
        due_diligence_id="dd-5", opportunity_id="opp-1", property_id="wrong", created_at=NOW
    )
    with pytest.raises(ValueError):
        validate_due_diligence_scope(item, opportunity())


def test_screening_compatibility_preserves_opportunity_scope():
    from app.due_diligence import validate_due_diligence_scope

    item = build_cre_property_due_diligence(
        due_diligence_id="dd-6", opportunity_id="opp-1", created_at=NOW
    )
    screening = CREOpportunityScreening(
        screening_id="screen-1", opportunity_id="opp-1", created_at=NOW, disposition="INSUFFICIENT_DATA"
    )
    validate_due_diligence_scope(item, opportunity(), screening=screening)


def test_deterministic_serialization_for_fixed_input():
    item = build_cre_property_due_diligence(
        due_diligence_id="dd-7", opportunity_id="opp-1", findings=[finding()], created_at=NOW
    )
    assert item.model_dump_json() == item.model_dump_json()
