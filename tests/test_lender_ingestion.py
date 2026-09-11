from datetime import datetime, timezone

import pytest

from app.lender_ingestion import (
    LenderEvidenceIngestionError,
    capture_raw_lender_evidence,
    ingest_financing_terms,
    ingest_financing_terms_collection,
    ingest_lender_profile,
)

OBSERVED = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
SOURCE_DATE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def provenance():
    return {
        "source": "manual://lender-program-1",
        "source_date": SOURCE_DATE,
        "observed_at": OBSERVED,
        "freshness_status": "CURRENT",
        "verification_status": "UNVERIFIED",
    }


def terms_payload(**overrides):
    data = {
        "financing_id": "fin-1",
        "lender_id": "lender-1",
        "loan_type": "PERMANENT",
        "minimum_loan": 2_000_000,
        "maximum_loan": 20_000_000,
        "maximum_ltv": 0.75,
        "maximum_ltc": 0.80,
        "minimum_dscr": 1.25,
        "minimum_debt_yield": 0.08,
        "interest_rate": 0.065,
        "rate_type": "FIXED",
        "amortization_years": 30,
        "maturity_years": 10,
        "recourse": "NON_RECOURSE_WITH_STANDARD_CARVEOUTS",
        "conditions": ["Subject to underwriting"],
        "applicability": ["Industrial", "Washington"],
        "provenance": [provenance()],
    }
    data.update(overrides)
    return data


def test_valid_profile_ingests():
    profile = ingest_lender_profile({
        "lender_id": "lender-1",
        "name": "Example Capital",
        "lender_type": "PRIVATE_LENDER",
        "asset_types": ["INDUSTRIAL"],
        "geographies": ["WASHINGTON"],
        "provenance": [provenance()],
    })
    assert profile.name == "Example Capital"


def test_valid_terms_ingest_and_preserve_evidence_metadata():
    terms = ingest_financing_terms(terms_payload())
    assert terms.maximum_ltv == 0.75
    assert terms.provenance[0].source_date == SOURCE_DATE
    assert terms.provenance[0].observed_at == OBSERVED
    assert terms.provenance[0].verification_status == "UNVERIFIED"
    assert terms.applicability == ["Industrial", "Washington"]
    assert terms.conditions == ["Subject to underwriting"]


def test_missing_information_remains_unknown():
    terms = ingest_financing_terms(
        terms_payload(interest_rate=None, maximum_ltc=None, evidence_status="INCOMPLETE")
    )
    assert terms.interest_rate is None
    assert terms.maximum_ltc is None
    assert terms.evidence_status == "INCOMPLETE"


def test_invalid_evidence_is_rejected():
    with pytest.raises(LenderEvidenceIngestionError):
        ingest_financing_terms(terms_payload(maximum_ltv=1.1))


def test_authoritative_calculation_keys_are_rejected():
    with pytest.raises(LenderEvidenceIngestionError, match="cannot be supplied"):
        ingest_financing_terms(terms_payload(ltv=0.60))
    with pytest.raises(LenderEvidenceIngestionError, match="cannot be supplied"):
        ingest_financing_terms(terms_payload(annual_debt_service=500_000))


def test_conflicting_observations_are_preserved():
    first = terms_payload(financing_id="advertised", maximum_ltv=0.75)
    second = terms_payload(
        financing_id="quoted",
        maximum_ltv=0.65,
        conflict_status="UNRESOLVED",
        conflicting_financing_ids=["advertised"],
        evidence_status="CONTRADICTORY",
        applicability=["Specific deal"],
    )
    result = ingest_financing_terms_collection([first, second])
    assert [item.maximum_ltv for item in result] == [0.75, 0.65]
    assert result[1].conflict_status == "UNRESOLVED"


def test_raw_capture_does_not_interpret_or_mutate_input():
    payload = {"source": "manual://example", "claim": {"maximum_ltv": 0.75}}
    captured = capture_raw_lender_evidence(payload)
    assert captured == payload
    captured["claim"]["maximum_ltv"] = 0.65
    assert payload["claim"]["maximum_ltv"] == 0.75


def test_ingestion_is_deterministic():
    first = ingest_financing_terms(terms_payload()).model_dump(mode="json")
    second = ingest_financing_terms(terms_payload()).model_dump(mode="json")
    assert first == second


def test_no_financing_calculations_or_execution_surface():
    terms = ingest_financing_terms(terms_payload())
    for name in (
        "calculate_dscr", "calculate_ltv", "calculate_ltc", "calculate_debt_yield",
        "calculate_debt_service", "authorize", "select_lender", "rank_lenders",
        "recommend_lender", "execute_transaction", "deploy_capital",
    ):
        assert not hasattr(terms, name)
