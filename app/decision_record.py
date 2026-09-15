"""Durable institutional Decision Record boundary.

A Decision Record records an explicit human institutional decision in the
context of a specific Investment Case and governance state. It does not
create authority, execution capability, outcome state, or epistemic memory.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HumanDecision(str, Enum):
    """Explicit human decision states recorded by the institution."""

    NO_GO = "NO_GO"
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"


class DecisionRecord(BaseModel):
    """Immutable in-memory record of an explicit human institutional decision."""

    model_config = ConfigDict(frozen=True)

    decision_record_id: str = Field(min_length=1)
    decision_record_version: int = Field(default=1, ge=1)
    opportunity_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    case_version: int = Field(ge=1)
    decided_at: datetime

    decision_readiness_state: str = Field(min_length=1)
    decision_gate_state: str = Field(min_length=1)
    decision_gate_snapshot: Dict[str, Any] = Field(default_factory=dict)
    investment_case_ref: str = Field(min_length=1)

    decision: HumanDecision
    human_rationale: str = Field(min_length=1)
    decision_maker_role: str = Field(min_length=1)

    authorized: bool
    authorization_timestamp: Optional[datetime] = None

    conditions: List[str] = Field(default_factory=list)
    dissent: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    analytical_artifact_refs: List[str] = Field(default_factory=list)
    recorded_at: datetime
    history_metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        """Reject inconsistent authority metadata without granting authority."""
        if self.authorized and self.authorization_timestamp is None:
            raise ValueError("authorized decisions require authorization_timestamp")
        if self.decision != HumanDecision.CONDITIONAL_GO and self.conditions:
            raise ValueError("conditions are only valid for CONDITIONAL_GO decisions")
        if self.decision in {HumanDecision.GO, HumanDecision.CONDITIONAL_GO} and self.decision_gate_state != "OPEN_READY_FOR_HUMAN_AUTHORITY":
            raise ValueError("GO decisions require an OPEN_READY_FOR_HUMAN_AUTHORITY gate snapshot")


def build_decision_record(
    *,
    decision_record_id: str,
    opportunity_id: str,
    case_id: str,
    case_version: int,
    decided_at: datetime,
    decision_readiness_state: str,
    decision_gate_state: str,
    investment_case_ref: str,
    decision: HumanDecision | str,
    human_rationale: str,
    decision_maker_role: str,
    authorized: bool,
    authorization_timestamp: Optional[datetime] = None,
    decision_gate_snapshot: Optional[Dict[str, Any]] = None,
    conditions: Optional[List[str]] = None,
    dissent: Optional[List[str]] = None,
    evidence_refs: Optional[List[str]] = None,
    analytical_artifact_refs: Optional[List[str]] = None,
    decision_record_version: int = 1,
    recorded_at: Optional[datetime] = None,
    history_metadata: Optional[Dict[str, Any]] = None,
) -> DecisionRecord:
    """Create a Decision Record only from explicit human decision input.

    Decision Gate or Decision Readiness state is historical context only and
    can never be used by this function to infer authorization.
    """
    return DecisionRecord(
        decision_record_id=decision_record_id,
        decision_record_version=decision_record_version,
        opportunity_id=opportunity_id,
        case_id=case_id,
        case_version=case_version,
        decided_at=decided_at,
        decision_readiness_state=decision_readiness_state,
        decision_gate_state=decision_gate_state,
        decision_gate_snapshot=dict(decision_gate_snapshot or {}),
        investment_case_ref=investment_case_ref,
        decision=decision,
        human_rationale=human_rationale,
        decision_maker_role=decision_maker_role,
        authorized=authorized,
        authorization_timestamp=authorization_timestamp,
        conditions=list(conditions or []),
        dissent=list(dissent or []),
        evidence_refs=list(evidence_refs or []),
        analytical_artifact_refs=list(analytical_artifact_refs or []),
        recorded_at=recorded_at or decided_at,
        history_metadata=dict(history_metadata or {"immutable_in_memory": True}),
    )
