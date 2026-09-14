from app.capital_epistemic import (
    EpistemicStatus,
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


def subject(subject_id="security:ACME", listing_id="listing:ACME-XNYS", provider_id="provider-record"):
    return Subject(
        subject_id=subject_id,
        subject_type="security",
        security_id="security:ACME",
        listing_id=listing_id,
        provider_id=provider_id,
        ticker="ACME",
        exchange="NYSE",
        mic="XNYS",
    )


def raw(**overrides):
    values = dict(
        source_id="synthetic-source-a",
        subject=subject(),
        value=1000,
        observed_at="2026-09-10T12:00:00+00:00",
        effective_period="2026-09-10",
        published_at="2026-09-10T13:00:00+00:00",
        available_at="2026-09-10T13:00:00+00:00",
        retrieved_at="2026-09-10T14:00:00+00:00",
        revision_id="revision-1",
        usage=VALID_USAGE,
        raw_fingerprint="raw-001",
    )
    values.update(overrides)
    return RawObservation(**values)


def normalized(raw_observation=None, **overrides):
    item = NormalizedObservation(
        raw=raw_observation or raw(),
        value=1000,
        unit="USD",
        currency="USD",
        transformation="identity normalization",
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


def decision():
    return "2026-09-11T00:00:00+00:00"


def test_knowledge_state_requires_retrieval_for_institutional_knowability():
    retrieved = knowledge_state(raw(retrieved_at="2026-09-10T14:00:00+00:00"), decision())
    not_retrieved = knowledge_state(raw(retrieved_at="2026-09-11T01:00:00+00:00"), decision())
    assert retrieved.knowable is True
    assert not_retrieved.knowable is False
    assert retrieved.published_by_decision is True
    assert retrieved.available_by_decision is True
    assert not_retrieved.retrieved_by_decision is False


def test_publication_after_decision_is_not_knowable():
    state = knowledge_state(
        raw(published_at="2026-09-11T01:00:00+00:00", available_at="2026-09-11T01:00:00+00:00"),
        decision(),
    )
    assert state.knowable is False


def test_availability_after_decision_is_not_knowable():
    state = knowledge_state(
        raw(available_at="2026-09-11T01:00:00+00:00"),
        decision(),
    )
    assert state.knowable is False


def test_late_retrieval_is_not_historical_knowledge():
    observation = normalized(raw(retrieved_at="2026-09-11T01:00:00+00:00"))
    admission = admit_evidence(observation, validate_observation(observation), decision())
    assert admission.admitted is False
    assert admission.status is EpistemicStatus.INSUFFICIENT_EVIDENCE


def test_revision_relationship_preserves_original_and_revised_history():
    original = raw(revision_id="revision-1", value=100, raw_fingerprint="raw-original")
    revised = raw(
        revision_id="revision-2",
        revised_from_revision_id="revision-1",
        value=120,
        raw_fingerprint="raw-revised",
    )
    assert original.value == 100
    assert revised.value == 120
    assert revised.revised_from_revision_id == original.revision_id
    assert original.raw_fingerprint != revised.raw_fingerprint
    assert original.retrieved_at == "2026-09-10T14:00:00+00:00"
    assert revised.retrieved_at == "2026-09-10T14:00:00+00:00"


def test_revision_does_not_rewrite_earlier_knowledge_state():
    original = raw(revision_id="revision-1", value=100)
    revised = raw(
        revision_id="revision-2",
        revised_from_revision_id="revision-1",
        value=120,
        published_at="2026-09-12T13:00:00+00:00",
        available_at="2026-09-12T13:00:00+00:00",
        retrieved_at="2026-09-12T14:00:00+00:00",
    )
    original_state = knowledge_state(original, decision())
    revised_state = knowledge_state(revised, decision())
    assert original_state.knowable is True
    assert revised_state.knowable is False
    assert original.value == 100


def test_actual_competing_observations_block_admission():
    provider_a = normalized(raw(source_id="synthetic-provider-a", value=1000, raw_fingerprint="a"))
    provider_b = normalized(raw(source_id="synthetic-provider-b", value=1100, raw_fingerprint="b"))
    admission = admit_evidence(
        provider_a,
        validate_observation(provider_a),
        decision(),
        conflicting_observations=(provider_b,),
    )
    assert provider_a.raw.source_id != provider_b.raw.source_id
    assert provider_a.value != provider_b.value
    assert provider_a.raw.value == 1000
    assert provider_b.raw.value == 1100
    assert admission.status is EpistemicStatus.CONFLICTED
    assert admission.admitted is False


def test_same_value_from_two_sources_is_not_silently_a_conflict():
    provider_a = normalized(raw(source_id="synthetic-provider-a", value=1000, raw_fingerprint="a"))
    provider_b = normalized(raw(source_id="synthetic-provider-b", value=1000, raw_fingerprint="b"))
    admission = admit_evidence(
        provider_a,
        validate_observation(provider_a),
        decision(),
        conflicting_observations=(provider_b,),
    )
    assert admission.status is EpistemicStatus.VALID


def test_provider_replacement_produces_same_institutional_contract():
    provider_a = normalized(raw(source_id="synthetic-provider-a", provider_id="record-a"))
    provider_b = normalized(raw(source_id="synthetic-provider-b", provider_id="record-b"))
    assert provider_a.raw.subject.subject_id == provider_b.raw.subject.subject_id
    assert provider_a.raw.subject.provider_id != provider_b.raw.subject.provider_id
    assert validate_observation(provider_a).status is EpistemicStatus.VALID
    assert validate_observation(provider_b).status is EpistemicStatus.VALID


def test_ticker_is_not_subject_identity():
    observation = normalized(raw(subject=subject(subject_id="", listing_id="", provider_id="")))
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, decision())
    assert admission.status is EpistemicStatus.AMBIGUOUS


def test_multiple_listings_can_share_security_subject_without_overwrite():
    first = subject(listing_id="listing:ACME-XNYS")
    second = subject(listing_id="listing:ACME-XNAS")
    assert first.subject_id == second.subject_id
    assert first.listing_id != second.listing_id


def test_provider_identifier_is_metadata_not_institutional_identity():
    first = subject(provider_id="provider-a-record-1")
    second = subject(provider_id="provider-b-record-77")
    assert first.subject_id == second.subject_id
    assert first.provider_id != second.provider_id


def test_missing_provenance_blocks_admission():
    observation = normalized()
    admission = admit_evidence(
        observation,
        validate_observation(observation),
        decision(),
        provenance_available=False,
    )
    assert admission.status is EpistemicStatus.INSUFFICIENT_EVIDENCE
    assert admission.admitted is False


def test_stale_observation_blocks_admission():
    observation = normalized()
    admission = admit_evidence(observation, validate_observation(observation), decision(), stale=True)
    assert admission.status is EpistemicStatus.STALE


def test_semantic_interpretation_is_rejected_as_normalization():
    observation = normalized(
        transformation="attractive investment",
        transformation_kind="semantic",
    )
    validation = validate_observation(observation)
    assert validation.status is EpistemicStatus.REJECTED
    assert "semantic interpretation" in validation.reasons[0]


def test_raw_and_normalized_values_and_lineage_survive():
    observation = normalized(value=1.0, transformation="divide by 1000")
    assert observation.raw.value == 1000
    assert observation.value == 1.0
    assert observation.lineage()["raw_fingerprint"] == "raw-001"
    assert observation.lineage()["transformation"] == "divide by 1000"
    assert observation.lineage()["transformation_kind"] == "mechanical"


def test_restricted_storage_blocks_durable_evidence():
    restricted = UsageState(
        retrievable=True,
        storable=False,
        transformable=True,
        displayable=True,
        retainable=False,
        redistributable=False,
    )
    observation = normalized(raw(usage=restricted))
    admission = admit_evidence(observation, validate_observation(observation), decision())
    assert admission.status is EpistemicStatus.REJECTED


def test_unknown_usage_fails_closed():
    observation = normalized(raw(usage=UsageState(retrievable=True)))
    admission = admit_evidence(observation, validate_observation(observation), decision())
    assert admission.status is EpistemicStatus.REJECTED


def test_reproducibility_exposes_admission_inputs():
    observation = normalized()
    validation = validate_observation(observation)
    admission = admit_evidence(observation, validation, decision())
    evidence = build_evidence(observation, validation, admission)
    assert admission.admitted is True
    assert evidence.provenance["source_id"] == observation.raw.source_id
    assert evidence.provenance["subject_id"] == observation.raw.subject.subject_id
    assert evidence.provenance["observed_at"] == observation.raw.observed_at
    assert evidence.provenance["published_at"] == observation.raw.published_at
    assert evidence.provenance["available_at"] == observation.raw.available_at
    assert evidence.provenance["retrieved_at"] == observation.raw.retrieved_at
    assert evidence.provenance["revision_id"] == observation.raw.revision_id
    assert evidence.provenance["usage"] == observation.raw.usage
    assert evidence.admission.knowledge_state.knowable is True
    assert evidence.execution_authority is False


def test_execution_authority_remains_hard_false():
    observation = normalized()
    evidence = build_evidence(
        observation,
        validate_observation(observation),
        admit_evidence(observation, validate_observation(observation), decision()),
    )
    assert evidence.execution_authority is False


def test_temporal_context_requires_observation_or_effective_period():
    observation = normalized(raw(observed_at=None, effective_period=None))
    validation = validate_observation(observation)
    assert validation.status is EpistemicStatus.REJECTED
    assert "missing temporal context" in validation.reasons
