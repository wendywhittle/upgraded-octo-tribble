"""Canonical institutional domain contracts for AletheiaTelos.

These objects establish identity and relationships without adding execution
capability. They are deliberately lightweight so existing analytical engines
can adopt them incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class OpportunityStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    ANALYSIS_READY = "ANALYSIS_READY"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Opportunity:
    """A discovered object of evaluation, not evidence and not a decision."""

    opportunity_id: str
    source: str
    opportunity_type: str
    description: str
    discovered_at: str
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    provenance: Dict[str, Any] = field(default_factory=dict)
    evidence_ids: List[str] = field(default_factory=list)
    asset_or_security_id: Optional[str] = None
    version: int = 1

    def __post_init__(self) -> None:
        if not self.opportunity_id.strip():
            raise ValueError("opportunity_id is required")
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.opportunity_type.strip():
            raise ValueError("opportunity_type is required")
        if not self.description.strip():
            raise ValueError("description is required")
        if self.version < 1:
            raise ValueError("version must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "source": self.source,
            "opportunity_type": self.opportunity_type,
            "description": self.description,
            "discovered_at": self.discovered_at,
            "status": self.status.value,
            "provenance": dict(self.provenance),
            "evidence_ids": list(self.evidence_ids),
            "asset_or_security_id": self.asset_or_security_id,
            "version": self.version,
            "evidence_validated": bool(self.evidence_ids),
        }


class EvidenceKind(str, Enum):
    EVIDENCE = "evidence"
    ASSUMPTION = "assumption"
    CALCULATION = "calculation"
    SCENARIO = "scenario"
    SIMULATION = "simulation"


@dataclass(frozen=True)
class EvidenceReference:
    """A typed reference used to prevent epistemic category collapse."""

    reference_id: str
    kind: EvidenceKind
    value: Any
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConflictCoexistence:
    """Canonical disagreement record; agreement is not manufactured."""

    conflict_id: str
    investment_case_id: str
    participating_perspectives: List[str]
    disputed_proposition: str
    supporting_evidence: List[str] = field(default_factory=list)
    opposing_evidence: List[str] = field(default_factory=list)
    disagreement_type: str = "interpretive"
    status: str = "unresolved"
    resolution_explanation: Optional[str] = None


@dataclass(frozen=True)
class RiskSimulationContract:
    """Canonical contract separating independent simulation from calculation."""

    simulation_id: str
    investment_case_id: str
    methodology: str
    model_inputs: Dict[str, Any]
    scenarios: List[Any]
    assumptions: List[Any]
    outputs: Dict[str, Any]
    independent_of_agents: bool
    valid: bool
    timestamp: str
    version: int = 1
    independence_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionRecordReference:
    """Reference only; a formal Decision Record requires explicit human input."""

    decision_record_id: str
    investment_case_id: str
    case_version: int
    decision_gate_state: str
    human_decision_required: bool = True
    authorized: bool = False
    executed: bool = False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_opportunity(
    *,
    source: str = "analysis_request",
    opportunity_type: str = "research_question",
    description: str,
    asset_or_security_id: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None,
    opportunity_id: Optional[str] = None,
    discovered_at: Optional[str] = None,
) -> Opportunity:
    """Create an opportunity without asserting that it is evidence or investable."""
    return Opportunity(
        opportunity_id=opportunity_id or f"OPP-{uuid4().hex}",
        source=source,
        opportunity_type=opportunity_type,
        description=description,
        discovered_at=discovered_at or now_iso(),
        provenance=provenance or {"origin": source},
        asset_or_security_id=asset_or_security_id,
    )
