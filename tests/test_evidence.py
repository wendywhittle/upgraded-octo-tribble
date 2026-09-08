from datetime import datetime, timedelta, timezone

from app.evidence import apply_evidence_gate, validate_evidence, validate_agent_evidence


NOW = datetime(2026, 9, 8, 15, 0, tzinfo=timezone.utc)


def evidence(**overrides):
    item = {
        "evidence_id": "E1",
        "source": "verified-source",
        "claim": "Observed claim",
        "observed_at": (NOW - timedelta(minutes=5)).isoformat(),
        "retrieved_at": (NOW - timedelta(minutes=2)).isoformat(),
        "provenance": {"type": "external_source", "point_in_time": True},
    }
    item.update(overrides)
    return item


def agent(evidence_items):
    return {"agent_id": "quant", "direction": "LONG", "evidence": evidence_items}


def test_valid_evidence_is_decision_usable():
    result = validate_evidence(evidence(), now=NOW)
    assert result["valid"] is True
    assert result["decision_usable"] is True


def test_synthetic_demo_evidence_is_blocked():
    result = validate_evidence(evidence(provenance={"type": "synthetic_demo", "point_in_time": True}), now=NOW)
    assert result["decision_usable"] is False
    assert any("Synthetic demo" in error for error in result["errors"])


def test_stale_evidence_is_blocked():
    old = NOW - timedelta(days=2)
    result = validate_evidence(evidence(observed_at=old.isoformat(), retrieved_at=old.isoformat()), now=NOW)
    assert result["decision_usable"] is False
    assert any("stale" in error for error in result["errors"])


def test_invalid_timestamp_is_blocked():
    result = validate_evidence(evidence(observed_at="not-a-timestamp"), now=NOW)
    assert result["decision_usable"] is False


def test_retrieval_cannot_precede_observation():
    result = validate_evidence(evidence(
        observed_at=(NOW - timedelta(minutes=2)).isoformat(),
        retrieved_at=(NOW - timedelta(minutes=5)).isoformat(),
    ), now=NOW)
    assert result["decision_usable"] is False


def test_missing_evidence_is_not_usable():
    result = validate_agent_evidence(agent([]), now=NOW)
    assert result["usable"] is False
    assert result["status"] == "missing"


def test_gate_forces_unverified_agent_to_no_data():
    agents, validations = apply_evidence_gate([agent([evidence(provenance={"type": "synthetic_demo", "point_in_time": True})])], now=NOW)
    assert agents[0]["direction"] == "NO_DATA"
    assert agents[0]["pre_evidence_direction"] == "LONG"
    assert agents[0]["evidence_gate"] == "BLOCKED"
    assert validations[0]["usable"] is False
