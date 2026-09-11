from datetime import datetime, timezone

import pytest

from app.lender_intelligence import (
    FinancingTerms,
    LenderIntelligenceValidationError,
    LenderProfile,
    ProvenanceRecord,
    validate_financing_terms_collection,
    validate_lender_evidence,
)

OBSERVED = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
SOURCE_DATE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def provenance(**overrides):
    data = {
        "source": "https://example.test/lender-program",
        "source_date": SOURCE_DATE,
        "observed_at": OBSERVED,
        "freshness_status": "CURRENT",
        "verification_status": "UNVERIFIED",
    }
    data.update(overrides)
    return ProvenanceRecord(**data)


def make_terms(**overrides):
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
        "conditions": ["Subject to underwriting and appraisal"],
        "applicability": ["Industrial", "Pacific Northwest"],
        "provenance": [provenance()],
    }
    data.update(overrides)
    return FinancingTerms(**data)


def test_valid_lender_profile():
    profile = LenderProfile(
        lender_id="lender-1",
        name="Example Capital",
        lender_type="PRIVATE_LENDER",
        asset_types=["INDUSTRIAL", "NNN"],
        geographies=["WASHINGTON", "OREGON"],
        provenance=[provenance()],
    )
    assert profile.lender_id == "lender-1"
    assert profile.provenance[0].provenance == "SOURCE"


def test_valid_financing_terms():
    terms = make_terms()
    assert terms.maximum_ltv == 0.75
    assert terms.minimum_dscr == 1.25
    assert terms.evidence_status == "OBSERVED"


def test_provenance_source_dates_and_observation_are_preserved():
    terms = make_terms()
    record = terms.provenance[0]
    assert record.source == "https://example.test/lender-program"
    assert record.source_date == SOURCE_DATE
    assert record.observed_at == OBSERVED


def test_freshness_and_verification_metadata_are_preserved():
    record = provenance(freshness_status="STALE", verification_status="PARTIALLY_VERIFIED")
    assert record.freshness_status == "STALE"
    assert record.verification_status == "PARTIALLY_VERIFIED"


def test_unknown_freshness_is_explicit():
    record = provenance(freshness_status="UNKNOWN", source_date=None)
    assert record.freshness_status == "UNKNOWN"
    assert record.source_date is None


def test_unresolved_questions_conditional_and_incomplete_terms_are_preserved():
    terms = make_terms(
        evidence_status="CONDITIONAL",
        interest_rate=None,
        conditions=["Rate subject to credit approval"],
        unresolved_questions=["Final spread not yet quoted"],
    )
    assert terms.evidence_status == "CONDITIONAL"
    assert terms.interest_rate is None
    assert terms.unresolved_questions == ["Final spread not yet quoted"]

    incomplete = make_terms(
        financing_id="fin-2",
        evidence_status="INCOMPLETE",
        maximum_ltc=None,
        minimum_debt_yield=None,
    )
    assert incomplete.evidence_status == "INCOMPLETE"
    assert incomplete.maximum_ltc is None


def test_conflicting_terms_are_preserved_without_resolution():
    first = make_terms(maximum_ltv=0.75)
    second = make_terms(
        financing_id="fin-2",
        maximum_ltv=0.65,
        conflict_status="UNRESOLVED",
        conflicting_financing_ids=["fin-1"],
        evidence_status="CONTRADICTORY",
    )
    validate_financing_terms_collection([first, second])
    assert first.maximum_ltv == 0.75
    assert second.maximum_ltv == 0.65
    assert second.conflict_status == "UNRESOLVED"


def test_same_lender_conflicting_observations_can_coexist():
    advertised = make_terms(financing_id="advertised", maximum_ltv=0.75)
    quoted = make_terms(
        financing_id="quoted",
        maximum_ltv=0.65,
        conflict_status="UNRESOLVED",
        conflicting_financing_ids=["advertised"],
        evidence_status="CONTRADICTORY",
        applicability=["Specific deal"],
    )
    validate_financing_terms_collection([advertised, quoted])
    assert advertised.lender_id == quoted.lender_id
    assert advertised.maximum_ltv != quoted.maximum_ltv


def test_invalid_loan_range_rejected():
    with pytest.raises(ValueError, match="minimum_loan"):
        make_terms(minimum_loan=21_000_000, maximum_loan=20_000_000)


def test_invalid_ltv_ltc_rejected():
    with pytest.raises(ValueError):
        make_terms(maximum_ltv=1.01)
    with pytest.raises(ValueError):
        make_terms(maximum_ltc=-0.01)


def test_invalid_rate_rejected():
    with pytest.raises(ValueError):
        make_terms(interest_rate=-0.01)
    with pytest.raises(ValueError):
        make_terms(interest_rate=1.01)


def test_invalid_amortization_and_maturity_rejected():
    with pytest.raises(ValueError):
        make_terms(amortization_years=0)
    with pytest.raises(ValueError):
        make_terms(maturity_years=0)
    with pytest.raises(ValueError, match="amortization_years"):
        make_terms(amortization_years=5, maturity_years=10)


def test_invalid_provenance_dates_rejected():
    with pytest.raises(ValueError, match="review_by"):
        provenance(review_by=datetime(2026, 9, 9, tzinfo=timezone.utc))


def test_calculation_authority_cannot_leak_into_lender_evidence():
    with pytest.raises(LenderIntelligenceValidationError, match="cannot be supplied"):
        validate_lender_evidence([{"lender_id": "lender-1", "ltv": 0.60}])
    with pytest.raises(LenderIntelligenceValidationError, match="cannot be supplied"):
        validate_lender_evidence([{"minimum_dscr": 1.25, "annual_debt_service": 500_000}])


def test_contract_rejects_unknown_fields():
    with pytest.raises(ValueError):
        make_terms(unapproved_metric=1)


def test_unknown_conflict_reference_rejected():
    with pytest.raises(LenderIntelligenceValidationError, match="Unknown conflicting"):
        validate_financing_terms_collection([
            make_terms(conflict_status="UNRESOLVED", conflicting_financing_ids=["missing"])
        ])


def test_identical_inputs_are_deterministic():
    first = make_terms().model_dump(mode="json")
    second = make_terms().model_dump(mode="json")
    assert first == second


def test_no_workflow_or_authorization_or_lender_selection_surface():
    terms = make_terms()
    profile = LenderProfile(
        lender_id="lender-1",
        name="Example Capital",
        lender_type="PRIVATE_LENDER",
        provenance=[provenance()],
    )
    for obj in (terms, profile):
        assert not hasattr(obj, "authorize")
        assert not hasattr(obj, "deploy_capital")
        assert not hasattr(obj, "execute_transaction")
        assert not hasattr(obj, "select_lender")
        assert not hasattr(obj, "rank_lenders")
        assert not hasattr(obj, "recommend_lender")
