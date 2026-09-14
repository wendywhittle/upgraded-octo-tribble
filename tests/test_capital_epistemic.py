from app.capital_epistemic import (
    EpistemicStatus,
    KnowledgeState,
    NormalizedObservation,
    RawObservation,
    Subject,
    UsageState,
    admit_evidence,
    build_evidence,
    knowledge_state,
    validate_observation,
)


VALID_USAGE = UsageState(
    retrievable=True,
    storable=True,
    transformable=True,
    displayable=True,
    retainable=True,
    redistributable=False,
)


def raw(**overrides):
    values = dict(
        source_id="synthetic-source",
        subject=Subject(
            subject_id="synthetic:ACME",
            subject_type="security",
            security_id="security:ACME",
            listing_id="listing:ACME-XNYS",
            provider_id="synthetic-record-1",
            ticker="ACME",
            exchange="NYSE",
            mic="XNYS",
        ),
        value=1_000_000,
        observed_at="2026-09-10T12:00:00+00:00",
        effective_period="2026-09-10",
        published_at="2026-09-10T13:00:00+00:00",
        available_at="2026-09-10T13:00:00+00:00",
        retrieved_at="2026-09-10T14:00:00+00:00",
        usage=VALID_USAGE,
        raw_fingerprint="raw-001",
    )
    values.update(overrides)
    return RawObservation(**values)


def normalized(raw_observation=None, **overrides):
    item = NormalizedObservation(
        raw=raw_observation or raw(),
        value=1_000_000,
        unit="USD",
        currency="USD",
        transformation="identity",
    )
    if overrides:
        return NormalizedObservation(
            raw=overrides.get("raw", item.raw),
            value=overrides.get("value", item.value),
            unit=overrides.get("unit", item.unit),
            currency=overrides.get("currency", item.currency),
            transformation=overrides.get("transformation", item.transformation),
            transformation_kind=overrides.get("transformation_kind", item.transformation_kind),
        )
    return item


def test_happy_path_admits_evidence_and_preserves_lineage():
    observation = normalized()
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, "2026-09-11T00:00:00+00:00")
    evidence = build_evidence(observation, validation, admission)

    assert validation.status is EpistemicStatus.VALID
    assert admission.admitted is True
    assert evidence.execution_authority is False
    assert evidence.provenance["raw_fingerprint"] == "raw-001"
    assert evidence.provenance["transformation"]["transformation"] == "identity"


def test_missing_data_is_not_fabricated():
    observation = normalized(raw(value=None))
    validation = validate_observation(observation)
    assert validation.status is EpistemicStatus.REJECTED
    assert "missing observation value" in validation.reasons


def test_ambiguous_identity_cannot_be_admitted():
    subject = Subject(subject_id="", subject_type="security", ticker="ACME")
    observation = normalized(raw(subject=subject))
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, "2026-09-11T00:00:00+00:00")
    assert admission.status is EpistemicStatus.AMBIGUOUS


def test_ticker_alone_does_not_establish_subject_identity():
    subject = Subject(subject_id="", subject_type="security", ticker="ACME")
    observation = normalized(raw(subject=subject))
    admission = admit_evidence(observation, validate_observation(observation), "2026-09-11T00:00:00+00:00")
    assert admission.admitted is False
    assert admission.status is EpistemicStatus.AMBIGUOUS


def test_conflict_blocks_admission_without_selecting_a_source():
    observation = normalized()
    admission = admit_evidence(
        observation,
        validate_observation(observation),
        "2026-09-11T00:00:00+00:00",
        conflicted=True,
    )
    assert admission.status is EpistemicStatus.CONFLICTED


def test_stale_observation_blocks_admission():
    observation = normalized()
    admission = admit_evidence(
        observation,
        validate_observation(observation),
        "2026-09-11T00:00:00+00:00",
        stale=True,
    )
    assert admission.status is EpistemicStatus.STALE


def test_revision_metadata_does_not_erase_original():
    original = raw(revision_id="revision-1", value=100)
    revised = raw(revision_id="revision-2", value=120)
    assert original.value == 100
    assert revised.value == 120
    assert original.revision_id != revised.revision_id


def test_knowledge_state_preserves_decision_time_view():
    item = raw(
        published_at="2026-09-12T13:00:00+00:00",
        available_at="2026-09-12T13:00:00+00:00",
        retrieved_at="2026-09-12T13:30:00+00:00",
    )
    state = knowledge_state(item, "2026-09-12T12:00:00+00:00")
    assert isinstance(state, KnowledgeState)
    assert state.knowable is False
    assert state.retrieved_by_decision is False


def test_transformation_lineage_is_reproducible():
    observation = normalized(transformation="USD identity normalization")
    lineage = observation.lineage()
    assert lineage["raw_fingerprint"] == "raw-001"
    assert lineage["transformation_kind"] == "mechanical"


def test_semantic_interpretation_cannot_be_normalization():
    observation = normalized(
        transformation="financially attractive",
        transformation_kind="semantic",
    )
    validation = validate_observation(observation)
    assert validation.status is EpistemicStatus.REJECTED


def test_usage_restriction_blocks_durable_evidence():
    restricted = UsageState(
        retrievable=True,
        storable=False,
        transformable=True,
        displayable=True,
        retainable=False,
        redistributable=False,
    )
    observation = normalized(raw(usage=restricted))
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, "2026-09-11T00:00:00+00:00")
    assert admission.status is EpistemicStatus.REJECTED


def test_unknown_usage_fails_closed():
    observation = normalized(raw(usage=UsageState(retrievable=True)))
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, "2026-09-11T00:00:00+00:00")
    assert admission.status is EpistemicStatus.REJECTED


def test_missing_temporal_context_is_rejected():
    observation = normalized(raw(observed_at=None, effective_period=None))
    validation = validate_observation(observation)
    assert validation.status is EpistemicStatus.REJECTED


def test_execution_authority_is_hard_false():
    observation = normalized()
    evidence = build_evidence(
        observation,
        validate_observation(observation),
        admit_evidence(observation, validate_observation(observation), "2026-09-11T00:00:00+00:00"),
    )
    assert evidence.execution_authority is False
