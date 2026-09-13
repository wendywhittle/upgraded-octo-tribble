"""Typed institutional investment lifecycle contract.

This module defines lifecycle state and transition semantics only. It does not
execute transactions, grant investment authority, sign documents, move capital,
or mutate portfolios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, FrozenSet, Optional
from uuid import uuid4


class LifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUALIFIED = "QUALIFIED"
    EVIDENCE_READY = "EVIDENCE_READY"
    DECISION_READY = "DECISION_READY"
    TRANSACTION_READY = "TRANSACTION_READY"
    SIGNATURE_READY = "SIGNATURE_READY"
    HUMAN_AUTHORIZED = "HUMAN_AUTHORIZED"
    EXECUTED = "EXECUTED"
    HOLDING = "HOLDING"
    DISPOSITION_PENDING = "DISPOSITION_PENDING"
    DISPOSED = "DISPOSED"
    OUTCOME_OBSERVED = "OUTCOME_OBSERVED"
    ATTRIBUTED = "ATTRIBUTED"
    LEARNED = "LEARNED"
    NO_GO = "NO_GO"
    NO_DEAL = "NO_DEAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HOLD = "HOLD"
    INVESTIGATE = "INVESTIGATE"
    CONDITIONAL_GO = "CONDITIONAL_GO"


HUMAN_AUTHORITY_STATE = LifecycleState.HUMAN_AUTHORIZED
EXECUTION_STATE = LifecycleState.EXECUTED

# Generic automated transitions. HUMAN_AUTHORIZED and EXECUTED are deliberately
# excluded: reaching those states requires an external human/execution record,
# and this contract never grants authority or performs execution.
_TRANSITIONS: dict[LifecycleState, FrozenSet[LifecycleState]] = {
    LifecycleState.DISCOVERED: frozenset({
        LifecycleState.QUALIFIED,
        LifecycleState.INSUFFICIENT_EVIDENCE,
        LifecycleState.NO_GO,
        LifecycleState.INVESTIGATE,
    }),
    LifecycleState.QUALIFIED: frozenset({
        LifecycleState.EVIDENCE_READY,
        LifecycleState.INSUFFICIENT_EVIDENCE,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
        LifecycleState.INVESTIGATE,
    }),
    LifecycleState.EVIDENCE_READY: frozenset({
        LifecycleState.DECISION_READY,
        LifecycleState.INSUFFICIENT_EVIDENCE,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
        LifecycleState.INVESTIGATE,
    }),
    LifecycleState.DECISION_READY: frozenset({
        LifecycleState.TRANSACTION_READY,
        LifecycleState.CONDITIONAL_GO,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
        LifecycleState.INVESTIGATE,
    }),
    LifecycleState.CONDITIONAL_GO: frozenset({
        LifecycleState.TRANSACTION_READY,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
        LifecycleState.INVESTIGATE,
    }),
    LifecycleState.TRANSACTION_READY: frozenset({
        LifecycleState.SIGNATURE_READY,
        LifecycleState.NO_DEAL,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
    }),
    LifecycleState.SIGNATURE_READY: frozenset({
        LifecycleState.NO_DEAL,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
    }),
    LifecycleState.HOLD: frozenset({
        LifecycleState.INVESTIGATE,
        LifecycleState.DECISION_READY,
        LifecycleState.TRANSACTION_READY,
        LifecycleState.NO_GO,
        LifecycleState.NO_DEAL,
    }),
    LifecycleState.INVESTIGATE: frozenset({
        LifecycleState.QUALIFIED,
        LifecycleState.EVIDENCE_READY,
        LifecycleState.DECISION_READY,
        LifecycleState.INSUFFICIENT_EVIDENCE,
        LifecycleState.NO_GO,
        LifecycleState.HOLD,
    }),
    LifecycleState.HUMAN_AUTHORIZED: frozenset({LifecycleState.EXECUTED}),
    LifecycleState.EXECUTED: frozenset({LifecycleState.HOLDING}),
    LifecycleState.HOLDING: frozenset({LifecycleState.DISPOSITION_PENDING}),
    LifecycleState.DISPOSITION_PENDING: frozenset({LifecycleState.DISPOSED}),
    LifecycleState.DISPOSED: frozenset({LifecycleState.OUTCOME_OBSERVED}),
    LifecycleState.OUTCOME_OBSERVED: frozenset({LifecycleState.ATTRIBUTED}),
    LifecycleState.ATTRIBUTED: frozenset({LifecycleState.LEARNED}),
}

_AUTHORITY_STATES = frozenset({LifecycleState.HUMAN_AUTHORIZED})
_EXECUTION_STATES = frozenset({LifecycleState.EXECUTED})
_TERMINAL_STATES = frozenset({
    LifecycleState.NO_GO,
    LifecycleState.NO_DEAL,
    LifecycleState.INSUFFICIENT_EVIDENCE,
    LifecycleState.LEARNED,
})


@dataclass(frozen=True)
class LifecycleTransition:
    """Immutable historical transition record."""

    from_state: Optional[LifecycleState]
    to_state: LifecycleState
    at: datetime
    reason: str


@dataclass(frozen=True)
class InstitutionalLifecycle:
    """Immutable lifecycle snapshot with append-only transition history."""

    opportunity_id: str
    current_state: LifecycleState = LifecycleState.DISCOVERED
    history: tuple[LifecycleTransition, ...] = field(default_factory=tuple)

    @classmethod
    def create(cls, opportunity_id: Optional[str] = None) -> "InstitutionalLifecycle":
        stable_id = opportunity_id or f"OPP-{uuid4().hex[:16]}"
        if not stable_id.strip():
            raise ValueError("opportunity_id must be non-empty")
        return cls(opportunity_id=stable_id)

    def transition(
        self,
        to_state: LifecycleState,
        reason: str,
        *,
        at: Optional[datetime] = None,
    ) -> "InstitutionalLifecycle":
        """Record an allowed non-authority transition.

        This method never grants human authority and never performs execution.
        HUMAN_AUTHORIZED and EXECUTED must be recorded by future explicit
        external authority/execution boundaries, not inferred here.
        """
        if not isinstance(to_state, LifecycleState):
            raise TypeError("to_state must be a LifecycleState")
        if not reason.strip():
            raise ValueError("reason must be non-empty")
        if to_state in _AUTHORITY_STATES or to_state in _EXECUTION_STATES:
            raise PermissionError(
                f"{to_state.value} cannot be reached by automated lifecycle transition"
            )
        if self.current_state in _TERMINAL_STATES:
            raise ValueError(f"Cannot transition from terminal state {self.current_state.value}")
        allowed = _TRANSITIONS.get(self.current_state, frozenset())
        if to_state not in allowed:
            raise ValueError(
                f"Illegal lifecycle transition: {self.current_state.value} -> {to_state.value}"
            )
        timestamp = at or datetime.now(timezone.utc)
        entry = LifecycleTransition(self.current_state, to_state, timestamp, reason)
        return InstitutionalLifecycle(
            opportunity_id=self.opportunity_id,
            current_state=to_state,
            history=self.history + (entry,),
        )

    @property
    def has_investment_authority(self) -> bool:
        """Lifecycle state never itself grants investment authority."""
        return False

    @property
    def has_execution_authority(self) -> bool:
        """Lifecycle state never itself grants execution authority."""
        return False

    @property
    def is_terminal(self) -> bool:
        return self.current_state in _TERMINAL_STATES

    @property
    def ready_for_human_signature(self) -> bool:
        return self.current_state is LifecycleState.SIGNATURE_READY


def allowed_transitions(state: LifecycleState) -> FrozenSet[LifecycleState]:
    """Return the immutable transition set for inspection/testing."""
    return _TRANSITIONS.get(state, frozenset())


def lifecycle_state_from_decision_gate(decision_gate: dict[str, Any]) -> LifecycleState:
    """Map analytical Decision Gate output to the lifecycle boundary.

    The Decision Gate's OPEN_READY_FOR_HUMAN_AUTHORITY state means analytical
    readiness only, so it maps to DECISION_READY. It never maps to transaction
    readiness, signature readiness, HUMAN_AUTHORIZED, or EXECUTED. Evidence
    hard stops and closed synthesis outcomes remain explicit blocked states.
    """
    if not isinstance(decision_gate, dict):
        raise TypeError("decision_gate must be a dictionary")

    hard_stops = decision_gate.get("hard_stops", [])
    if "NO_USABLE_EVIDENCE" in hard_stops or "EVIDENCE_VALIDATION_FAILED" in hard_stops:
        return LifecycleState.INSUFFICIENT_EVIDENCE

    if decision_gate.get("state") == "OPEN_READY_FOR_HUMAN_AUTHORITY":
        return LifecycleState.DECISION_READY

    verdict = str(decision_gate.get("system_synthesis_verdict") or "").upper()
    outcome_map = {
        "NO_DATA": LifecycleState.INSUFFICIENT_EVIDENCE,
        "NO_GO": LifecycleState.NO_GO,
        "NO DEAL": LifecycleState.NO_DEAL,
        "NO_DEAL": LifecycleState.NO_DEAL,
        "HOLD": LifecycleState.HOLD,
        "INVESTIGATE": LifecycleState.INVESTIGATE,
        "CONDITIONAL GO": LifecycleState.CONDITIONAL_GO,
        "CONDITIONAL_GO": LifecycleState.CONDITIONAL_GO,
    }
    return outcome_map.get(verdict, LifecycleState.NO_GO)
