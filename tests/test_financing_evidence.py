from datetime import datetime, timezone

import pytest

from app.financing_evidence import financing_observation_to_evidence
from app.financing_observation import FinancingObservation


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def validated_observation(**overrides):
    values = {
        "observation_id": "fin-1",
        "provider_id": "provider-alpha",
        "observed_at": "2026-09-15T11:55:00+00:00",
        "source_uri": "https://example.invalid/source",
        "source_label": "Provider financing sheet",
        "financing_type": "bridge",
        "asset_classes": ["industrial"],
        "geography": ["Portland Metro"],
        "loan_to_value": 70.0,
        "interest_rate": "floating",
        "term": "24 months",
        "amortization": "interest-only",
        "covenants": ["DSCR covenant"],
        "assumptions": ["stabilization within 18 months"],
        "limitations": ["indicative only"],
        "validation_status": "VALIDATED",
        "evidence_id": "E-FIN-1",
    }
    values.update(overrides)
    return FinancingObservation(**values)


def test_unvalidated_observation_cannot_cross_boundary():
    observation = validated_observation(validation_status="UNVALIDATED", evidence_id=None)
    with pytest.raises(ValueError, match="Only VALIDATED"):
        financing_observation_to_evidence(observation, now=NOW)


def test_validated_financing_observation_becomes_existing_evidence_shape():
    evidence = financing_observation_to_evidence(validated_observation(), now=NOW)
    assert evidence["evidence_id"] == "E-FIN-1"
    assert evidence["source"] == "https://example.invalid/source"
    assert evidence["observed_at"] == "2026-09-15T11:55:00+00:00"
    assert evidence["provenance"]["provider_id"] == "provider-alpha"
    assert evidence["provenance"]["observation_id"] == "fin-1"
    assert evidence["claim"]["loan_to_value"] == 70.0
    assert evidence["claim"]["assumptions"] == ["stabilization within 18 months"]
    assert evidence["claim"]["limitations"] == ["indicative only"]
    assert evidence["evidence_validation"]["decision_usable"] is True


def test_provider_identity_and_terms_are_provider_independent():
    for provider_id in ("private-lender", "bank", "family-office", "institutional-debt", "equity-provider", "strategic-capital"):
        evidence = financing_observation_to_evidence(
            validated_observation(provider_id=provider_id),
            now=NOW,
        )
        assert evidence["provenance"]["provider_id"] == provider_id
        assert evidence["claim"]["financing_type"] == "bridge"


def test_source_label_is_preserved_when_uri_is_missing():
    evidence = financing_observation_to_evidence(
        validated_observation(source_uri=None),
        now=NOW,
    )
    assert evidence["source"] == "Provider financing sheet"
    assert evidence["provenance"]["source_label"] == "Provider financing sheet"


def test_validated_but_stale_financing_evidence_remains_blocked():
    with pytest.raises(ValueError, match="stale"):
        financing_observation_to_evidence(
            validated_observation(observed_at="2026-09-10T11:55:00+00:00"),
            now=NOW,
            max_age_seconds=60,
            retrieved_at="2026-09-10T11:56:00+00:00",
        )


def test_financing_evidence_contains_no_authority_path():
    evidence = financing_observation_to_evidence(validated_observation(), now=NOW)
    assert "investment_authority" not in evidence
    assert "execution_authority" not in evidence
    assert "portfolio_mutation" not in evidence
