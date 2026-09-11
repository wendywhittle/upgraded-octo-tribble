"""Institutional CRE workflow domain, authorization gates, and append-only audit trail.

This module is intentionally small and provider-independent. It establishes the
workflow spine around the existing intelligence components without replacing them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    DEAL_DISCOVERED = "DEAL_DISCOVERED"
    SCREENED = "SCREENED"
    AWAITING_UNDERWRITING_APPROVAL = "AWAITING_UNDERWRITING_APPROVAL"
    UNDERWRITING = "UNDERWRITING"
    SIMULATION = "SIMULATION"
    CONTRARIAN_REVIEW = "CONTRARIAN_REVIEW"
    CAPITAL_STACK_ANALYSIS = "CAPITAL_STACK_ANALYSIS"
    AWAITING_CAPITAL_APPROVAL = "AWAITING_CAPITAL_APPROVAL"
    INVESTMENT_COMMITTEE = "INVESTMENT_COMMITTEE"
    AWAITING_INVESTMENT_APPROVAL = "AWAITING_INVESTMENT_APPROVAL"
    APPROVED = "APPROVED"
    PORTFOLIO_CREATED = "PORTFOLIO_CREATED"
    MONITORING = "MONITORING"
    OUTCOME_OBSERVED = "OUTCOME_OBSERVED"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"
    NO_GO = "NO_GO"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    SIMULATION_FAILED = "SIMULATION_FAILED"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"


class ActorType(str, Enum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class AuthorizationGate(str, Enum):
    UNDERWRITING = "UNDERWRITING"
    CAPITAL_STRUCTURE = "CAPITAL_STRUCTURE"
    INVESTMENT = "INVESTMENT"


class AuthorizationDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class Opportunity(BaseModel):
    opportunity_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class Deal(BaseModel):
    deal_id: str = Field(default_factory=lambda: str(uuid4()))
    opportunity: Opportunity
    state: WorkflowState = WorkflowState.DEAL_DISCOVERED
    version: int = 1
    created_at: str = Field(default_factory=lambda: utc_now())
    updated_at: str = Field(default_factory=lambda: utc_now())


class Authorization(BaseModel):
    authorization_id: str = Field(default_factory=lambda: str(uuid4()))
    deal_id: str
    gate: AuthorizationGate
    decision: AuthorizationDecision
    actor: str
    actor_type: ActorType
    timestamp: str = Field(default_factory=lambda: utc_now())
    reason: str
    approved_object_version: int
    scope: Dict[str, Any] = Field(default_factory=dict)
    audit_reference: Optional[str] = None


class InvestmentCase(BaseModel):
    """Stable envelope for future CRE engines; fields remain provider-neutral."""

    deal_id: str
    version: int = 1
    opportunity: Optional[Dict[str, Any]] = None
    asset: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    operating_model: Optional[Dict[str, Any]] = None
    proforma: Optional[Dict[str, Any]] = None
    financing: Optional[Dict[str, Any]] = None
    capital_stack: Optional[Dict[str, Any]] = None
    valuation: Optional[Dict[str, Any]] = None
    cash_flows: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None
    sensitivities: Optional[Dict[str, Any]] = None
    scenarios: Optional[Dict[str, Any]] = None
    simulation_results: Optional[Dict[str, Any]] = None
    risk_metrics: Optional[Dict[str, Any]] = None
    contrarian_findings: List[Dict[str, Any]] = Field(default_factory=list)
    margin_of_safety: Optional[Dict[str, Any]] = None
    investment_thesis: Optional[Dict[str, Any]] = None
    agent_perspectives: List[Dict[str, Any]] = Field(default_factory=list)
    disagreement: List[Dict[str, Any]] = Field(default_factory=list)
    investment_committee_output: Optional[Dict[str, Any]] = None
    human_authorizations: List[str] = Field(default_factory=list)
    workflow_state: WorkflowState = WorkflowState.DEAL_DISCOVERED
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    deal_id: str
    timestamp: str = Field(default_factory=lambda: utc_now())
    actor: str
    actor_type: ActorType
    previous_state: Optional[WorkflowState] = None
    new_state: Optional[WorkflowState] = None
    authorization_reference: Optional[str] = None
    reason: Optional[str] = None
    object_version: int
    system_version: str = "1.11.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowError(ValueError):
    """Raised when a workflow operation violates a domain invariant."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Only these transitions are legal. Gate states are deliberately explicit.
_ALLOWED_TRANSITIONS: Dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.DEAL_DISCOVERED: {
        WorkflowState.SCREENED,
        WorkflowState.REJECTED,
        WorkflowState.NO_GO,
    },
    WorkflowState.SCREENED: {
        WorkflowState.AWAITING_UNDERWRITING_APPROVAL,
        WorkflowState.REJECTED,
        WorkflowState.NO_GO,
    },
    WorkflowState.AWAITING_UNDERWRITING_APPROVAL: {
        WorkflowState.UNDERWRITING,
        WorkflowState.REJECTED,
        WorkflowState.NO_GO,
    },
    WorkflowState.UNDERWRITING: {
        WorkflowState.SIMULATION,
        WorkflowState.BLOCKED,
        WorkflowState.INSUFFICIENT_DATA,
        WorkflowState.VALIDATION_FAILED,
        WorkflowState.NO_GO,
    },
    WorkflowState.SIMULATION: {
        WorkflowState.CONTRARIAN_REVIEW,
        WorkflowState.SIMULATION_FAILED,
        WorkflowState.BLOCKED,
        WorkflowState.NO_GO,
    },
    WorkflowState.CONTRARIAN_REVIEW: {
        WorkflowState.CAPITAL_STACK_ANALYSIS,
        WorkflowState.CONTRADICTORY_EVIDENCE,
        WorkflowState.NO_GO,
    },
    WorkflowState.CAPITAL_STACK_ANALYSIS: {
        WorkflowState.AWAITING_CAPITAL_APPROVAL,
        WorkflowState.BLOCKED,
        WorkflowState.VALIDATION_FAILED,
        WorkflowState.NO_GO,
    },
    WorkflowState.AWAITING_CAPITAL_APPROVAL: {
        WorkflowState.INVESTMENT_COMMITTEE,
        WorkflowState.REJECTED,
        WorkflowState.NO_GO,
    },
    WorkflowState.INVESTMENT_COMMITTEE: {
        WorkflowState.AWAITING_INVESTMENT_APPROVAL,
        WorkflowState.BLOCKED,
        WorkflowState.NO_GO,
    },
    WorkflowState.AWAITING_INVESTMENT_APPROVAL: {
        WorkflowState.APPROVED,
        WorkflowState.REJECTED,
        WorkflowState.NO_GO,
    },
    WorkflowState.APPROVED: {WorkflowState.PORTFOLIO_CREATED},
    WorkflowState.PORTFOLIO_CREATED: {WorkflowState.MONITORING},
    WorkflowState.MONITORING: {
        WorkflowState.OUTCOME_OBSERVED,
        WorkflowState.BLOCKED,
    },
    WorkflowState.OUTCOME_OBSERVED: {WorkflowState.ARCHIVED},
    WorkflowState.ARCHIVED: set(),
    WorkflowState.REJECTED: {WorkflowState.ARCHIVED},
    WorkflowState.NO_GO: {WorkflowState.ARCHIVED},
    WorkflowState.BLOCKED: set(),
    WorkflowState.INSUFFICIENT_DATA: {WorkflowState.BLOCKED, WorkflowState.NO_GO},
    WorkflowState.VALIDATION_FAILED: {WorkflowState.BLOCKED, WorkflowState.NO_GO},
    WorkflowState.CALCULATION_ERROR: {WorkflowState.BLOCKED},
    WorkflowState.SIMULATION_FAILED: {WorkflowState.BLOCKED, WorkflowState.NO_GO},
    WorkflowState.CONTRADICTORY_EVIDENCE: {WorkflowState.BLOCKED, WorkflowState.NO_GO},
    WorkflowState.AUTHORIZATION_REQUIRED: set(),
}

_REQUIRED_GATE_FOR_DESTINATION = {
    WorkflowState.UNDERWRITING: AuthorizationGate.UNDERWRITING,
    WorkflowState.INVESTMENT_COMMITTEE: AuthorizationGate.CAPITAL_STRUCTURE,
    WorkflowState.APPROVED: AuthorizationGate.INVESTMENT,
}


class WorkflowStore:
    """Append-only JSONL event store used until a stronger persistence layer is justified."""

    def __init__(self, path: Path | str = Path("data/workflow_events.jsonl")) -> None:
        self.path = Path(path)

    def append(self, event: Dict[str, Any] | BaseModel) -> None:
        payload = event.model_dump(mode="json") if isinstance(event, BaseModel) else event
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def events(self, deal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        result: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                if deal_id is None or event.get("deal_id") == deal_id:
                    result.append(event)
        return result


class WorkflowService:
    def __init__(self, store: Optional[WorkflowStore] = None, system_version: str = "1.11.0") -> None:
        self.store = store or WorkflowStore()
        self.system_version = system_version

    def create_deal(self, opportunity: Opportunity, actor: str = "system") -> Deal:
        deal = Deal(opportunity=opportunity)
        self.store.append(
            AuditEvent(
                event_type="DEAL_CREATED",
                deal_id=deal.deal_id,
                actor=actor,
                actor_type=ActorType.SYSTEM,
                new_state=deal.state,
                object_version=deal.version,
                system_version=self.system_version,
                metadata={"opportunity_id": opportunity.opportunity_id},
            )
        )
        return deal

    def _current_deal(self, deal_id: str) -> Deal:
        events = self.store.events(deal_id)
        if not events:
            raise WorkflowError(f"Unknown deal: {deal_id}")
        first = events[0]
        if first.get("event_type") != "DEAL_CREATED":
            raise WorkflowError(f"Workflow history for {deal_id} is invalid")
        opportunity = Opportunity(**first["metadata"]["opportunity"])
        state = WorkflowState(first["new_state"])
        version = int(first["object_version"])
        created_at = first["timestamp"]
        updated_at = created_at
        for event in events[1:]:
            if event.get("event_type") == "STATE_TRANSITIONED":
                state = WorkflowState(event["new_state"])
                version = int(event["object_version"])
                updated_at = event["timestamp"]
        return Deal(
            deal_id=deal_id,
            opportunity=opportunity,
            state=state,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_deal(self, deal_id: str) -> Deal:
        return self._current_deal(deal_id)

    def authorize(
        self,
        deal_id: str,
        gate: AuthorizationGate,
        decision: AuthorizationDecision,
        actor: str,
        actor_type: ActorType,
        reason: str,
        scope: Optional[Dict[str, Any]] = None,
    ) -> Authorization:
        deal = self._current_deal(deal_id)
        if actor_type is not ActorType.HUMAN:
            raise WorkflowError("Human authorization is required; agents and systems cannot authorize gates")
        if not actor.strip():
            raise WorkflowError("Human actor is required")
        if not reason.strip():
            raise WorkflowError("Authorization reason is required")

        expected_state = {
            AuthorizationGate.UNDERWRITING: WorkflowState.AWAITING_UNDERWRITING_APPROVAL,
            AuthorizationGate.CAPITAL_STRUCTURE: WorkflowState.AWAITING_CAPITAL_APPROVAL,
            AuthorizationGate.INVESTMENT: WorkflowState.AWAITING_INVESTMENT_APPROVAL,
        }[gate]
        if deal.state is not expected_state:
            raise WorkflowError(f"Gate {gate.value} is not available from state {deal.state.value}")

        authorization = Authorization(
            deal_id=deal_id,
            gate=gate,
            decision=decision,
            actor=actor,
            actor_type=actor_type,
            reason=reason,
            approved_object_version=deal.version,
            scope=scope or {},
        )
        self.store.append(
            AuditEvent(
                event_type="HUMAN_AUTHORIZATION_RECORDED",
                deal_id=deal_id,
                actor=actor,
                actor_type=actor_type,
                authorization_reference=authorization.authorization_id,
                reason=reason,
                object_version=deal.version,
                system_version=self.system_version,
                metadata={"gate": gate.value, "decision": decision.value, "scope": authorization.scope},
            )
        )
        authorization.audit_reference = self.store.events(deal_id)[-1]["event_id"]
        return authorization

    def transition(
        self,
        deal_id: str,
        new_state: WorkflowState,
        actor: str,
        actor_type: ActorType,
        reason: str,
        authorization_id: Optional[str] = None,
    ) -> Deal:
        deal = self._current_deal(deal_id)
        allowed = _ALLOWED_TRANSITIONS.get(deal.state, set())
        if new_state not in allowed:
            raise WorkflowError(f"Illegal transition: {deal.state.value} -> {new_state.value}")

        required_gate = _REQUIRED_GATE_FOR_DESTINATION.get(new_state)
        if required_gate is not None:
            if not authorization_id:
                raise WorkflowError(f"Human authorization required for {new_state.value}")
            self._require_approved_authorization(deal_id, authorization_id, required_gate, deal.version)

        next_version = deal.version + 1
        event = AuditEvent(
            event_type="STATE_TRANSITIONED",
            deal_id=deal_id,
            actor=actor,
            actor_type=actor_type,
            previous_state=deal.state,
            new_state=new_state,
            authorization_reference=authorization_id,
            reason=reason,
            object_version=next_version,
            system_version=self.system_version,
        )
        self.store.append(event)
        return self._current_deal(deal_id)

    def _require_approved_authorization(
        self, deal_id: str, authorization_id: str, gate: AuthorizationGate, object_version: int
    ) -> None:
        for event in reversed(self.store.events(deal_id)):
            if event.get("event_type") != "HUMAN_AUTHORIZATION_RECORDED":
                continue
            if event.get("authorization_reference") != authorization_id:
                continue
            metadata = event.get("metadata", {})
            if metadata.get("gate") != gate.value or metadata.get("decision") != AuthorizationDecision.APPROVE.value:
                raise WorkflowError("Authorization does not approve the required gate")
            if int(event["object_version"]) != object_version:
                raise WorkflowError("Authorization does not match the current deal version")
            return
        raise WorkflowError("Authorization not found for deal")

    def authorizations(self, deal_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.store.events(deal_id) if e.get("event_type") == "HUMAN_AUTHORIZATION_RECORDED"]

    def audit(self, deal_id: str) -> List[Dict[str, Any]]:
        return self.store.events(deal_id)
