from datetime import datetime, timezone

import pytest

from app.decision_record import DecisionRecord, HumanDecision, build_decision_record


NOW = datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc)


def record(**overrides):
    values = {
        "decision_record_id": "decision:case-001:v1:001",
        "case_id": "case-001",
        "case_version": 1,
        "decided_at": NOW,
        "decision_readiness_state": "READY_FOR_HUMAN_AUTHORITY",
        "decision_gate_state": "OPEN_READY_FOR_HUMAN_AUTHORITY",
        "investment_case_ref": "case-001:v1",
        "decision": HumanDecision.NO_GO,
        "human_rationale": "The Investment Committee declined the opportunity.",
        "decision_maker_role": "Investment Committee",
        "authorized": False,
    }
    values.update(overrides)
    return build_decision_record(**values)


def test_explicit_human_no_go_is_recorded():
    result = record()
    assert result.decision == HumanDecision.NO_GO
    assert result.authorized is False
    assert result.decision_maker_role == "Investment Committee"


def test_explicit_human_go_is_recorded_as_authorized():
    result = record(
        decision=HumanDecision.GO,
        authorized=True,
        authorization_timestamp=NOW,
        human_rationale="The Investment Committee approved the case.",
    )
    assert result.decision == HumanDecision.GO
    assert result.authorized is True
    assert result.authorization_timestamp == NOW


def test_conditional_go_preserves_conditions():
    result = record(
        decision=HumanDecision.CONDITIONAL_GO,
        authorized=True,
        authorization_timestamp=NOW,
        conditions=["Proceed only if financing remains within approved limits."],
    )
    assert result.decision == HumanDecision.CONDITIONAL_GO
    assert result.conditions == ["Proceed only if financing remains within approved limits."]


def test_ready_gate_does_not_infer_authorization():
    result = record(
        decision_readiness_state="READY_FOR_HUMAN_AUTHORITY",
        decision_gate_state="OPEN_READY_FOR_HUMAN_AUTHORITY",
        authorized=False,
    )
    assert result.authorized is False
    assert result.authorization_timestamp is None


def test_recommendation_or_gate_state_is_not_a_decision_record_input():
    result = record(
        decision_readiness_state="READY_FOR_HUMAN_AUTHORITY",
        decision_gate_state="OPEN_READY_FOR_HUMAN_AUTHORITY",
    )
    assert result.decision == HumanDecision.NO_GO
    assert result.human_rationale


def test_exact_case_and_governance_context_is_preserved():
    result = record(
        case_id="case-xyz",
        case_version=7,
        investment_case_ref="case-xyz:v7",
        decision_readiness_state="READY_FOR_HUMAN_AUTHORITY",
        decision_gate_state="OPEN_READY_FOR_HUMAN_AUTHORITY",
    )
    assert result.case_id == "case-xyz"
    assert result.case_version == 7
    assert result.investment_case_ref == "case-xyz:v7"
    assert result.decision_readiness_state == "READY_FOR_HUMAN_AUTHORITY"
    assert result.decision_gate_state == "OPEN_READY_FOR_HUMAN_AUTHORITY"


def test_decision_record_is_immutable():
    result = record()
    with pytest.raises((TypeError, ValueError)):
        result.decision = HumanDecision.GO


def test_authorized_requires_explicit_timestamp():
    with pytest.raises(ValueError, match="authorization_timestamp"):
        record(decision=HumanDecision.GO, authorized=True)


def test_conditions_are_only_valid_for_conditional_go():
    with pytest.raises(ValueError, match="CONDITIONAL_GO"):
        record(conditions=["Condition"])


def test_decision_record_has_no_execution_capability():
    result = record()
    assert not hasattr(result, "execute")
    assert not hasattr(result, "transaction")
    assert not hasattr(result, "position")
    assert not hasattr(result, "portfolio_mutation")
