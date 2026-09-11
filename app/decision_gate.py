"""Formal Decision Gate governance boundary for AletheiaTelos.

The gate certifies analytical readiness only. It never authorizes an investment,
executes capital movement, or creates a human decision.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Sequence


class GateState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"


class CriterionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class HardStop(str, Enum):
    CRITICAL_EVIDENCE_GAP = "CRITICAL_EVIDENCE_GAP"
    UNVERIFIED_MATERIAL_ASSUMPTION = "UNVERIFIED_MATERIAL_ASSUMPTION"
    UNDERWRITING_INCOMPLETE = "UNDERWRITING_INCOMPLETE"
    CONTRARIAN_REVIEW_INCOMPLETE = "CONTRARIAN_REVIEW_INCOMPLETE"
    MISSING_DOWNSIDE_TAIL_ANALYSIS = "MISSING_DOWNSIDE_TAIL_ANALYSIS"
    BLOCKING_CONFLICT = "BLOCKING_CONFLICT"
    UNCLASSIFIED_MATERIAL_UNKNOWN = "UNCLASSIFIED_MATERIAL_UNKNOWN"
    GOVERNANCE_FAILURE = "GOVERNANCE_FAILURE"
    INCOMPLETE_DECISION_RECORD = "INCOMPLETE_DECISION_RECORD"


class HumanDisposition(str, Enum):
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    REQUEST_MORE_DILIGENCE = "REQUEST MORE DILIGENCE"
    REVISE_ASSUMPTIONS = "REVISE ASSUMPTIONS"
    DECLINE = "DECLINE"
    NO_INVESTMENT = "NO INVESTMENT"


MANDATORY_CRITERIA: tuple[str, ...] = (
    "OPPORTUNITY_DEFINED",
    "EVIDENCE_INTEGRITY",
    "UNDERWRITING_COMPLETE",
    "MULTI_PERSPECTIVE_CHALLENGE_COMPLETE",
    "CONTRARIAN_REVIEW_COMPLETE",
    "SCENARIO_ANALYSIS_COMPLETE",
    "CONFLICTS_CHARACTERIZED",
    "MATERIAL_UNKNOWNS_CLASSIFIED",
    "GOVERNANCE_CHECK_PASSED",
    "DECISION_RECORD_COMPLETE",
)

HARD_STOP_FOR_CRITERION: dict[str, HardStop] = {
    "EVIDENCE_INTEGRITY": HardStop.CRITICAL_EVIDENCE_GAP,
    "UNDERWRITING_COMPLETE": HardStop.UNDERWRITING_INCOMPLETE,
    "CONTRARIAN_REVIEW_COMPLETE": HardStop.CONTRARIAN_REVIEW_INCOMPLETE,
    "SCENARIO_ANALYSIS_COMPLETE": HardStop.MISSING_DOWNSIDE_TAIL_ANALYSIS,
    "CONFLICTS_CHARACTERIZED": HardStop.BLOCKING_CONFLICT,
    "MATERIAL_UNKNOWNS_CLASSIFIED": HardStop.UNCLASSIFIED_MATERIAL_UNKNOWN,
    "GOVERNANCE_CHECK_PASSED": HardStop.GOVERNANCE_FAILURE,
    "DECISION_RECORD_COMPLETE": HardStop.INCOMPLETE_DECISION_RECORD,
}


@dataclass(frozen=True)
class GateAuditEvent:
    timestamp: str
    from_state: GateState | None
    to_state: GateState
    readiness_criteria: Mapping[str, CriterionStatus]
    blocking_conditions: Sequence[str] = field(default_factory=tuple)
    reason: str | None = None


@dataclass(frozen=True)
class DecisionGateResult:
    state: GateState
    readiness_criteria: Mapping[str, CriterionStatus]
    blocking_conditions: Sequence[str] = field(default_factory=tuple)
    hard_stops: Sequence[HardStop] = field(default_factory=tuple)
    ready_for_human_authority: bool = False
    system_can_authorize: bool = False
    system_recommendation: str | None = None
    audit_event: GateAuditEvent | None = None

    @property
    def display_status(self) -> str:
        return (
            "READY FOR HUMAN AUTHORITY"
            if self.state is GateState.OPEN
            else "GATE CLOSED"
        )


@dataclass(frozen=True)
class HumanDecisionRecord:
    disposition: HumanDisposition
    rationale: str
    authority: str = "HUMAN"
    exception_acknowledged: bool = False
    system_gate_state: GateState = GateState.OPEN
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.authority != "HUMAN":
            raise ValueError("decision authority must be HUMAN")
        if not self.rationale.strip():
            raise ValueError("human decision rationale is required")
        if self.system_gate_state is GateState.CLOSED and not self.exception_acknowledged:
            raise ValueError("a closed gate requires an explicit human exception acknowledgement")


def evaluate_decision_gate(
    criteria: Mapping[str, CriterionStatus | str | bool],
    *,
    previous_state: GateState | None = None,
    system_recommendation: str | None = None,
) -> DecisionGateResult:
    """Evaluate readiness deterministically using independent mandatory criteria.

    Missing or invalid criteria fail closed. Recommendation, confidence, consensus,
    urgency, and expected return are intentionally not inputs to gate readiness.
    """
    normalized: dict[str, CriterionStatus] = {}
    for name in MANDATORY_CRITERIA:
        value = criteria.get(name)
        if isinstance(value, CriterionStatus):
            normalized[name] = value
        elif isinstance(value, bool):
            normalized[name] = CriterionStatus.PASS if value else CriterionStatus.FAIL
        elif isinstance(value, str):
            try:
                normalized[name] = CriterionStatus(value.upper())
            except ValueError:
                normalized[name] = CriterionStatus.FAIL
        else:
            normalized[name] = CriterionStatus.FAIL

    failed = tuple(name for name in MANDATORY_CRITERIA if normalized[name] is CriterionStatus.FAIL)
    stops: list[HardStop] = []
    if "OPPORTUNITY_DEFINED" in failed:
        stops.append(HardStop.CRITICAL_EVIDENCE_GAP)
    for criterion in failed:
        stop = HARD_STOP_FOR_CRITERION.get(criterion)
        if stop is not None and stop not in stops:
            stops.append(stop)

    blocking = tuple(stops)
    state = GateState.OPEN if not failed else GateState.CLOSED
    reopened = previous_state is GateState.OPEN and state is GateState.CLOSED
    event = GateAuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        from_state=previous_state,
        to_state=state,
        readiness_criteria=normalized,
        blocking_conditions=tuple(stop.value for stop in stops),
        reason="MATERIAL CHANGE / ANALYSIS INVALIDATED" if reopened else None,
    )
    return DecisionGateResult(
        state=state,
        readiness_criteria=normalized,
        blocking_conditions=blocking,
        hard_stops=tuple(stops),
        ready_for_human_authority=state is GateState.OPEN,
        system_can_authorize=False,
        system_recommendation=system_recommendation,
        audit_event=event,
    )


def record_human_decision(
    disposition: HumanDisposition | str,
    rationale: str,
    *,
    gate_state: GateState,
    exception_acknowledged: bool = False,
) -> HumanDecisionRecord:
    """Record an explicitly supplied human disposition without creating one in-system."""
    if isinstance(disposition, str):
        disposition = HumanDisposition(disposition)
    return HumanDecisionRecord(
        disposition=disposition,
        rationale=rationale,
        system_gate_state=gate_state,
        exception_acknowledged=exception_acknowledged,
    )
