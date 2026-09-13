from datetime import datetime, timezone

from app.decision_gate import build_decision_gate
from app.opportunity_acquisition import RawObservation, normalize_observation
from app.opportunity_evidence import (
    opportunity_to_evidence_candidate,
    opportunity_to_evidence_candidates,
    validate_opportunity_evidence_candidate,
)


def opportunity():
    return normalize_observation(
        RawObservation(
            source="fixture",
            source_url="https://example.invalid/opportunity/1",
            observed_at="2026-09-12T20:00:00+00:00",
            payload={
                "asset_type": "industrial",
                "location": "Vancouver, WA",
                "asking_price": 10000000,
                "claim": "The source lists an asking price of $10,000,000.",
                "raw_source_reference": "fixture-record-1",
                "property_attributes": {"noi": 700000},
            },
        )
    )


def test_opportunity_produces_pending_evidence_candidate_with_distinct_identity():
    candidate = opportunity_to_evidence_candidate(opportunity())
    assert candidate["opportunity_id"].startswith("OPP-")
    assert candidate["evidence_id"].startswith("EVID-CAND-")
    assert candidate["evidence_id"] != candidate["opportunity_id"]
    assert candidate["evidence_status"] == "EVIDENCE_CANDIDATE"
    assert candidate["validation_status"] == "PENDING"
    assert candidate["decision_usable"] is False


def test_candidate_preserves_source_provenance_and_claim_material():
    candidate = opportunity_to_evidence_candidate(opportunity())
    assert candidate["source"] == "fixture"
    assert candidate["source_url"] == "https://example.invalid/opportunity/1"
    assert candidate["observed_at"] == "2026-09-12T20:00:00+00:00"
    assert candidate["raw_source_reference"] == "fixture-record-1"
    assert candidate["provenance"]["source"] == "fixture"
    assert candidate["claim"] == "The source lists an asking price of $10,000,000."


def test_candidate_is_not_validated_until_explicit_validation_step():
    candidate = opportunity_to_evidence_candidate(opportunity())
    assert candidate["validation_status"] == "PENDING"
    assert "validation" not in candidate

    result = validate_opportunity_evidence_candidate(
        candidate,
        now=datetime(2026, 9, 12, 21, 0, tzinfo=timezone.utc),
    )
    assert result["validation_status"] == "VALIDATED"
    assert result["decision_usable"] is True
    assert result["validation"]["decision_usable"] is True


def test_insufficient_provenance_remains_blocked_by_existing_validator():
    item = opportunity()
    item["provenance"] = None
    candidate = opportunity_to_evidence_candidate(item)
    result = validate_opportunity_evidence_candidate(
        candidate,
        now=datetime(2026, 9, 12, 21, 0, tzinfo=timezone.utc),
    )
    assert result["validation_status"] == "BLOCKED"
    assert result["decision_usable"] is False
    assert any("provenance" in error.lower() for error in result["validation"]["errors"])


def test_missing_claim_does_not_invent_evidence_and_remains_unusable():
    item = opportunity()
    item["claim"] = None
    candidate = opportunity_to_evidence_candidate(item)
    assert candidate["claim"] is None
    assert candidate["classification"] == "UNRESOLVED_QUESTION"
    result = validate_opportunity_evidence_candidate(
        candidate,
        now=datetime(2026, 9, 12, 21, 0, tzinfo=timezone.utc),
    )
    assert result["decision_usable"] is False
    assert result["validation_status"] == "BLOCKED"


def test_candidate_batch_is_only_a_pending_handoff():
    candidates = opportunity_to_evidence_candidates([opportunity()])
    assert len(candidates) == 1
    assert candidates[0]["validation_status"] == "PENDING"
    assert candidates[0]["decision_usable"] is False


def test_handoff_governance_cannot_open_decision_gate():
    candidate = opportunity_to_evidence_candidate(opportunity())
    assert candidate["research_only"] is True
    assert candidate["human_authority_required"] is True
    assert candidate["autonomous_execution"] is False
    assert candidate["brokerage_connectivity"] is False
    assert candidate["portfolio_mutation"] is False
    assert candidate["investment_authority"] is False

    gate = build_decision_gate(
        evidence={"count": 1, "usable_count": 0, "validation": []},
        conflicts={"conflicts": [], "horizon_divergences": []},
        simulation={"valid": True},
        skeptic={"valid": True},
        synthesis={"verdict": "INVESTIGATE"},
        governance={
            "autonomous_execution": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
            "investment_authority": False,
        },
    )
    assert gate["state"] == "CLOSED_BLOCKED"
    assert gate["ready_for_human_authority"] is False
