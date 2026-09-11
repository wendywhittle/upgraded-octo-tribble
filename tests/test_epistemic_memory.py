from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.epistemic_memory import ContradictionRecord, EpistemicRecord, EpistemicRevision


NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)


def make_record(record_type="knowledge", **overrides):
    data = {
        "record_id": "knowledge:001",
        "record_type": record_type,
        "created_at": NOW,
        "source_refs": ["evidence:001"],
        "provenance": {"source": "test"},
        "content": {"statement": "occupancy is 91%"},
    }
    data.update(overrides)
    return EpistemicRecord(**data)


def test_typed_epistemic_records_preserve_taxonomy():
    for record_type in (
        "evidence", "knowledge", "assumption", "hypothesis", "calculation",
        "interpretation", "recommendation", "authorization", "outcome", "attribution", "lesson",
    ):
        assert make_record(record_type).record_type == record_type


def test_invalid_record_type_is_rejected():
    with pytest.raises(ValidationError):
        make_record("decision")


def test_provenance_and_dates_are_preserved():
    record = make_record(effective_at=NOW, observed_at=NOW)
    assert record.source_refs == ["evidence:001"]
    assert record.provenance == {"source": "test"}
    assert record.effective_at == NOW
    assert record.observed_at == NOW


def test_record_is_immutable():
    record = make_record()
    with pytest.raises(ValidationError):
        record.status = "superseded"


def test_revision_is_explicit_and_points_to_prior_record():
    revision = EpistemicRevision(
        revision_id="revision:001",
        prior_record_id="assumption:001",
        new_record_id="assumption:002",
        reason="New lease evidence changed the assumption",
        evidence_refs=["evidence:009"],
        created_at=NOW,
    )
    assert revision.prior_record_id == "assumption:001"
    assert revision.new_record_id == "assumption:002"


def test_contradiction_preserves_all_positions_without_resolution():
    contradiction = ContradictionRecord(
        record_id="contradiction:001",
        subject_record_ids=["claim:broker", "claim:lease"],
        description="Conflicting occupancy claims",
        created_at=NOW,
    )
    assert contradiction.status == "unresolved"
    assert contradiction.subject_record_ids == ["claim:broker", "claim:lease"]
    assert contradiction.resolution_record_id is None


def test_contradiction_requires_at_least_two_positions():
    with pytest.raises(ValidationError):
        ContradictionRecord(
            record_id="contradiction:bad",
            subject_record_ids=["claim:only-one"],
            description="Not actually a contradiction",
            created_at=NOW,
        )


def test_memory_has_no_authority():
    record = make_record("authorization")
    assert record.has_authority is False
