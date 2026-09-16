import pytest

from app.financing_observation import FinancingObservation


def test_unvalidated_observation_is_not_evidence():
    observation = FinancingObservation(
        observation_id="obs-1",
        provider_id="prideco_loans",
        observed_at="2026-09-15T12:00:00Z",
        financing_type="bridge",
        loan_to_value=70.0,
    )

    assert observation.validation_status == "UNVALIDATED"
    assert observation.evidence_id is None
    assert observation.is_validated_evidence is False


def test_validated_observation_requires_evidence_id():
    with pytest.raises(ValueError, match="require evidence_id"):
        FinancingObservation(
            observation_id="obs-2",
            provider_id="prideco_loans",
            observed_at="2026-09-15T12:00:00Z",
            validation_status="VALIDATED",
        )


def test_validated_observation_can_cross_evidence_boundary():
    observation = FinancingObservation(
        observation_id="obs-3",
        provider_id="future_provider",
        observed_at="2026-09-15T12:00:00Z",
        financing_type="construction",
        loan_to_cost=75.0,
        validation_status="VALIDATED",
        evidence_id="evidence-123",
    )

    assert observation.is_validated_evidence is True
    assert observation.normalized()["provider_id"] == "future_provider"


def test_financing_metrics_are_bounded():
    with pytest.raises(ValueError, match="loan_to_value"):
        FinancingObservation(
            observation_id="obs-4",
            provider_id="provider",
            observed_at="2026-09-15T12:00:00Z",
            loan_to_value=101.0,
        )
