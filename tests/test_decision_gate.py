import pytest

from app.decision_gate import (
    CriterionStatus,
    GateState,
    HardStop,
    HumanDisposition,
    MANDATORY_CRITERIA,
    evaluate_decision_gate,
    record_human_decision,
)


def passing_criteria():
    return {name: CriterionStatus.PASS for name in MANDATORY_CRITERIA}


def test_all_mandatory_criteria_pass_opens_gate():
    result = evaluate_decision_gate(passing_criteria(), system_recommendation="PROCEED")
    assert result.state is GateState.OPEN
    assert result.ready_for_human_authority is True
    assert result.system_can_authorize is False
    assert result.system_recommendation == "PROCEED"


def test_one_failed_criterion_closes_gate():
    criteria = passing_criteria()
    criteria["EVIDENCE_INTEGRITY"] = CriterionStatus.FAIL
    result = evaluate_decision_gate(criteria)
    assert result.state is GateState.CLOSED
    assert "EVIDENCE_INTEGRITY" in result.readiness_criteria
    assert HardStop.CRITICAL_EVIDENCE_GAP in result.hard_stops


def test_multiple_failures_are_preserved():
    criteria = passing_criteria()
    criteria["UNDERWRITING_COMPLETE"] = False
    criteria["GOVERNANCE_CHECK_PASSED"] = False
    result = evaluate_decision_gate(criteria)
    assert result.state is GateState.CLOSED
    assert HardStop.UNDERWRITING_INCOMPLETE in result.hard_stops
    assert HardStop.GOVERNANCE_FAILURE in result.hard_stops


def test_confidence_and_recommendation_cannot_open_failed_gate():
    criteria = passing_criteria()
    criteria["SCENARIO_ANALYSIS_COMPLETE"] = False
    result = evaluate_decision_gate(criteria, system_recommendation="PROCEED")
    assert result.state is GateState.CLOSED
    assert result.system_recommendation == "PROCEED"


def test_consensus_is_not_a_gate_input():
    result = evaluate_decision_gate(passing_criteria())
    assert result.state is GateState.OPEN
    assert not hasattr(result, "consensus_score")


def test_human_exception_does_not_rewrite_failed_gate():
    criteria = passing_criteria()
    criteria["EVIDENCE_INTEGRITY"] = False
    result = evaluate_decision_gate(criteria)
    decision = record_human_decision(
        HumanDisposition.PROCEED,
        "Human accepts the evidence limitation for further review.",
        gate_state=result.state,
        exception_acknowledged=True,
    )
    assert result.state is GateState.CLOSED
    assert decision.system_gate_state is GateState.CLOSED
    assert decision.exception_acknowledged is True
    assert decision.authority == "HUMAN"


def test_closed_gate_requires_explicit_exception_for_human_decision():
    with pytest.raises(ValueError):
        record_human_decision(
            HumanDisposition.PROCEED,
            "Proceed anyway.",
            gate_state=GateState.CLOSED,
        )


def test_human_decision_is_independent_of_system_recommendation():
    result = evaluate_decision_gate(passing_criteria(), system_recommendation="PROCEED")
    decision = record_human_decision(
        HumanDisposition.DECLINE,
        "Human declines despite the system recommendation.",
        gate_state=result.state,
    )
    assert decision.disposition is HumanDisposition.DECLINE
    assert result.system_recommendation == "PROCEED"


def test_no_investment_is_valid_terminal_disposition():
    decision = record_human_decision(
        HumanDisposition.NO_INVESTMENT,
        "Margin of safety is insufficient.",
        gate_state=GateState.OPEN,
    )
    assert decision.disposition is HumanDisposition.NO_INVESTMENT


def test_open_gate_recloses_after_material_change():
    opened = evaluate_decision_gate(passing_criteria(), previous_state=GateState.CLOSED)
    criteria = passing_criteria()
    criteria["EVIDENCE_INTEGRITY"] = False
    reopened = evaluate_decision_gate(criteria, previous_state=opened.state)
    assert opened.state is GateState.OPEN
    assert reopened.state is GateState.CLOSED
    assert reopened.audit_event is not None
    assert reopened.audit_event.reason == "MATERIAL CHANGE / ANALYSIS INVALIDATED"


def test_missing_criteria_fail_closed():
    result = evaluate_decision_gate({})
    assert result.state is GateState.CLOSED
    assert len(result.blocking_conditions) > 0


def test_governance_failure_is_a_hard_stop():
    criteria = passing_criteria()
    criteria["GOVERNANCE_CHECK_PASSED"] = False
    result = evaluate_decision_gate(criteria)
    assert result.state is GateState.CLOSED
    assert HardStop.GOVERNANCE_FAILURE in result.hard_stops


def test_system_cannot_create_human_authority():
    result = evaluate_decision_gate(passing_criteria())
    assert result.system_can_authorize is False
    assert result.audit_event is not None
    assert result.audit_event.to_state is GateState.OPEN
    assert not hasattr(result, "human_decision")


def test_gate_transition_is_auditable():
    result = evaluate_decision_gate(passing_criteria(), previous_state=GateState.CLOSED)
    event = result.audit_event
    assert event is not None
    assert event.from_state is GateState.CLOSED
    assert event.to_state is GateState.OPEN
    assert len(event.readiness_criteria) == len(MANDATORY_CRITERIA)
