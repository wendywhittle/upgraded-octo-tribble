from datetime import datetime, timezone

import pytest

from app.decision_gate import build_decision_gate
from app.institutional_lifecycle import (
    InstitutionalLifecycle,
    LifecycleState,
    allowed_transitions,
    lifecycle_state_from_decision_gate,
)

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


def test_end_state_path_preserves_immutable_history():
    lifecycle = InstitutionalLifecycle.create("OPP-001")
    qualified = lifecycle.transition(LifecycleState.QUALIFIED, "Opportunity qualified", at=NOW)
    evidence = qualified.transition(LifecycleState.EVIDENCE_READY, "Evidence validated", at=NOW)
    decision = evidence.transition(LifecycleState.DECISION_READY, "Decision package ready", at=NOW)
    transaction = decision.transition(LifecycleState.TRANSACTION_READY, "Transaction package ready", at=NOW)
    signature = transaction.transition(LifecycleState.SIGNATURE_READY, "Signature package assembled", at=NOW)

    assert lifecycle.opportunity_id == qualified.opportunity_id == signature.opportunity_id == "OPP-001"
    assert lifecycle.current_state is LifecycleState.DISCOVERED
    assert len(lifecycle.history) == 0
    assert signature.ready_for_human_signature is True
    assert signature.has_investment_authority is False
    assert signature.has_execution_authority is False
    assert len(signature.history) == 5
    assert signature.history[-1].to_state is LifecycleState.SIGNATURE_READY


def test_ready_authorized_and_executed_are_distinct_and_not_automatically_reachable():
    lifecycle = InstitutionalLifecycle.create("OPP-002")
    for state, reason in [
        (LifecycleState.QUALIFIED, "qualified"),
        (LifecycleState.EVIDENCE_READY, "evidence ready"),
        (LifecycleState.DECISION_READY, "decision ready"),
        (LifecycleState.TRANSACTION_READY, "transaction ready"),
        (LifecycleState.SIGNATURE_READY, "signature ready"),
    ]:
        lifecycle = lifecycle.transition(state, reason, at=NOW)

    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.HUMAN_AUTHORIZED, "authorization")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "execution")

    assert lifecycle.current_state is LifecycleState.SIGNATURE_READY
    assert lifecycle.ready_for_human_signature is True
    assert lifecycle.has_investment_authority is False
    assert lifecycle.has_execution_authority is False


def test_illegal_transition_is_rejected():
    lifecycle = InstitutionalLifecycle.create("OPP-003")
    with pytest.raises(PermissionError, match="cannot be reached by automated lifecycle transition"):
        lifecycle.transition(LifecycleState.EXECUTED, "skip all gates")


def test_legitimate_blocked_outcomes_are_supported():
    for outcome in (
        LifecycleState.NO_GO,
        LifecycleState.NO_DEAL,
        LifecycleState.INSUFFICIENT_EVIDENCE,
        LifecycleState.HOLD,
        LifecycleState.INVESTIGATE,
        LifecycleState.CONDITIONAL_GO,
    ):
        assert outcome in LifecycleState

    lifecycle = InstitutionalLifecycle.create("OPP-004")
    blocked = lifecycle.transition(LifecycleState.INSUFFICIENT_EVIDENCE, "Missing primary evidence", at=NOW)
    assert blocked.is_terminal is True
    with pytest.raises(ValueError, match="terminal state"):
        blocked.transition(LifecycleState.QUALIFIED, "new evidence")


def test_history_is_immutable_and_identity_is_stable():
    lifecycle = InstitutionalLifecycle.create("OPP-005")
    next_lifecycle = lifecycle.transition(LifecycleState.QUALIFIED, "qualified", at=NOW)

    assert lifecycle.opportunity_id == next_lifecycle.opportunity_id
    assert lifecycle.history == ()
    assert len(next_lifecycle.history) == 1
    assert next_lifecycle.history[0].reason == "qualified"


def test_authority_and_execution_states_are_defined_but_not_granted():
    assert allowed_transitions(LifecycleState.HUMAN_AUTHORIZED) == frozenset({LifecycleState.EXECUTED})
    assert allowed_transitions(LifecycleState.EXECUTED) == frozenset({LifecycleState.HOLDING})
    lifecycle = InstitutionalLifecycle.create("OPP-006")
    assert lifecycle.has_investment_authority is False
    assert lifecycle.has_execution_authority is False


def _gate(verdict="NO_DATA", governance=None, usable_count=0, validation=None):
    return build_decision_gate(
        evidence={
            "count": usable_count,
            "usable_count": usable_count,
            "validation": validation or [],
        },
        conflicts={"conflicts": [], "horizon_divergences": []},
        simulation={"valid": True},
        skeptic={"valid": True},
        synthesis={"verdict": verdict},
        governance=governance or {
            "human_decision_required": True,
            "autonomous_execution": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
            "investment_authority": False,
        },
    )


def test_blocked_decision_gate_maps_to_insufficient_evidence():
    gate = _gate()
    assert gate["state"] == "CLOSED_BLOCKED"
    assert lifecycle_state_from_decision_gate(gate) is LifecycleState.INSUFFICIENT_EVIDENCE


def test_ready_decision_gate_maps_only_to_decision_ready():
    gate = _gate(
        verdict="INVESTIGATE",
        usable_count=1,
        validation=[{"decision_usable": True}],
    )
    assert gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert gate["ready_for_human_authority"] is True
    assert lifecycle_state_from_decision_gate(gate) is LifecycleState.DECISION_READY


def test_decision_gate_mapping_preserves_blocked_outcomes():
    for verdict, expected in [
        ("NO_GO", LifecycleState.NO_GO),
        ("NO DEAL", LifecycleState.NO_DEAL),
        ("HOLD", LifecycleState.HOLD),
        ("INVESTIGATE", LifecycleState.INVESTIGATE),
        ("CONDITIONAL GO", LifecycleState.CONDITIONAL_GO),
    ]:
        gate = _gate(verdict=verdict, usable_count=1, validation=[{"decision_usable": True}])
        gate["state"] = "CLOSED_BLOCKED"
        assert lifecycle_state_from_decision_gate(gate) is expected


def test_decision_gate_mapping_preserves_governance_boundary():
    gate = _gate(
        verdict="INVESTIGATE",
        usable_count=1,
        validation=[{"decision_usable": True}],
    )
    assert gate["research_only"] is True
    assert gate["human_decision_required"] is True
    assert gate["autonomous_execution"] is False
    assert gate["brokerage_connectivity"] is False
    assert gate["portfolio_mutation"] is False
    assert gate["investment_authority"] is False
    assert lifecycle_state_from_decision_gate(gate) is LifecycleState.DECISION_READY

    lifecycle = InstitutionalLifecycle.create("OPP-GATE").transition(
        LifecycleState.QUALIFIED, "qualified", at=NOW
    ).transition(
        LifecycleState.EVIDENCE_READY, "evidence ready", at=NOW
    ).transition(
        LifecycleState.DECISION_READY, "decision ready", at=NOW
    )
    assert lifecycle.current_state is LifecycleState.DECISION_READY
    assert lifecycle.has_investment_authority is False
    assert lifecycle.has_execution_authority is False

    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "attempt execution")
