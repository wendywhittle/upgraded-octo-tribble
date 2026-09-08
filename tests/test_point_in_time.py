from datetime import datetime, timedelta, timezone

from app.evidence import validate_evidence


NOW = datetime(2026, 9, 8, 15, 0, tzinfo=timezone.utc)


def base_evidence():
    return {
        "evidence_id": "E1",
        "source": "source",
        "claim": "Observed claim",
        "observed_at": (NOW - timedelta(minutes=10)).isoformat(),
        "retrieved_at": (NOW - timedelta(minutes=5)).isoformat(),
        "provenance": {"type": "external_source", "point_in_time": True},
    }


def test_future_observation_is_blocked():
    item = base_evidence()
    item["observed_at"] = (NOW + timedelta(minutes=1)).isoformat()
    result = validate_evidence(item, now=NOW)
    assert result["decision_usable"] is False
    assert any("future" in error for error in result["errors"])


def test_future_retrieval_is_blocked():
    item = base_evidence()
    item["retrieved_at"] = (NOW + timedelta(minutes=1)).isoformat()
    result = validate_evidence(item, now=NOW)
    assert result["decision_usable"] is False


def test_point_in_time_provenance_must_be_explicit_for_clean_evidence():
    item = base_evidence()
    item["provenance"] = {"type": "external_source", "point_in_time": False}
    result = validate_evidence(item, now=NOW)
    assert result["decision_usable"] is True
    assert result["warnings"]
