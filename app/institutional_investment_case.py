"""Canonical Institutional Investment Case domain boundary.

The Investment Case assembles existing analytical outputs into a stable, versioned
institutional container. It does not replace evidence, underwriting, simulation,
perspectives, conflict analysis, the Decision Gate, or human authority.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class InvestmentCaseStatus(str, Enum):
    INVESTIGATE = "INVESTIGATE"
    NO_GO = "NO_GO"
    NO_DEAL = "NO_DEAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HOLD = "HOLD"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    READY_FOR_HUMAN_AUTHORITY = "READY_FOR_HUMAN_AUTHORITY"
    REASSESS = "REASSESS"
    MONITOR = "MONITOR"
    DISPOSITION_REVIEW = "DISPOSITION_REVIEW"


@dataclass
class InstitutionalInvestmentCase:
    """Versioned analytical container with no authorization or execution capability."""

    case_id: str
    case_version: int
    created_at: str
    updated_at: str
    status: InvestmentCaseStatus
    investment_question: str
    domain: str = "shared"
    opportunity: Any = None
    identity: Any = None
    evidence: List[Any] = field(default_factory=list)
    claims: List[Any] = field(default_factory=list)
    thesis: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[Any] = field(default_factory=list)
    calculations: Any = None
    valuation: Any = None
    scenarios: Any = None
    risk: Any = None
    perspectives: Any = None
    conflicts: Any = None
    contrarian_review: Any = None
    decision_readiness: Any = None
    decision_options: List[str] = field(default_factory=list)
    governance: Dict[str, Any] = field(default_factory=dict)
    decision_record_ref: Optional[str] = None
    monitoring_ref: Optional[str] = None
    reassessment_ref: Optional[str] = None
    disposition_ref: Optional[str] = None
    outcome_ref: Optional[str] = None
    attribution_ref: Optional[str] = None
    epistemic_memory_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")
        if self.case_version < 1:
            raise ValueError("case_version must be >= 1")
        if not self.investment_question or not self.investment_question.strip():
            raise ValueError("investment_question is required")
        if self.domain not in {"shared", "capital", "asset"}:
            raise ValueError("domain must be one of: shared, capital, asset")

    @property
    def ready_for_human_authority(self) -> bool:
        return self.status == InvestmentCaseStatus.READY_FOR_HUMAN_AUTHORITY

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialization-safe projection without adding authority fields."""
        return {
            "case_id": self.case_id,
            "case_version": self.case_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "investment_question": self.investment_question,
            "domain": self.domain,
            "opportunity": self.opportunity,
            "identity": self.identity,
            "evidence": self.evidence,
            "claims": self.claims,
            "thesis": self.thesis,
            "assumptions": self.assumptions,
            "calculations": self.calculations,
            "valuation": self.valuation,
            "scenarios": self.scenarios,
            "risk": self.risk,
            "perspectives": self.perspectives,
            "conflicts": self.conflicts,
            "contrarian_review": self.contrarian_review,
            "decision_readiness": self.decision_readiness,
            "decision_options": self.decision_options,
            "governance": self.governance,
            "decision_record_ref": self.decision_record_ref,
            "monitoring_ref": self.monitoring_ref,
            "reassessment_ref": self.reassessment_ref,
            "disposition_ref": self.disposition_ref,
            "outcome_ref": self.outcome_ref,
            "attribution_ref": self.attribution_ref,
            "epistemic_memory_ref": self.epistemic_memory_ref,
            "research_only": True,
            "human_decision_required": True,
            "human_authorization": None,
            "authorized": False,
            "executed": False,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_from_outputs(evidence: Dict[str, Any], gate: Dict[str, Any], synthesis: Dict[str, Any]) -> InvestmentCaseStatus:
    if evidence.get("usable_count", 0) <= 0:
        return InvestmentCaseStatus.INSUFFICIENT_EVIDENCE
    if gate.get("ready_for_human_authority"):
        return InvestmentCaseStatus.READY_FOR_HUMAN_AUTHORITY

    verdict = str(synthesis.get("verdict", "INVESTIGATE")).upper()
    mapping = {
        "NO_GO": InvestmentCaseStatus.NO_GO,
        "NO-GO": InvestmentCaseStatus.NO_GO,
        "NO_DEAL": InvestmentCaseStatus.NO_DEAL,
        "NO DEAL": InvestmentCaseStatus.NO_DEAL,
        "HOLD": InvestmentCaseStatus.HOLD,
        "CONDITIONAL GO": InvestmentCaseStatus.CONDITIONAL_GO,
        "CONDITIONAL_GO": InvestmentCaseStatus.CONDITIONAL_GO,
        "INVESTIGATE": InvestmentCaseStatus.INVESTIGATE,
        "NO_DATA": InvestmentCaseStatus.INSUFFICIENT_EVIDENCE,
    }
    return mapping.get(verdict, InvestmentCaseStatus.INVESTIGATE)


def build_institutional_investment_case(
    question: str,
    *,
    opportunity: Any = None,
    identity: Any = None,
    evidence: Optional[List[Any]] = None,
    evidence_summary: Optional[Dict[str, Any]] = None,
    claims: Optional[List[Any]] = None,
    thesis: Optional[Dict[str, Any]] = None,
    assumptions: Optional[List[Any]] = None,
    calculations: Any = None,
    valuation: Any = None,
    scenarios: Any = None,
    risk: Any = None,
    perspectives: Any = None,
    conflicts: Any = None,
    contrarian_review: Any = None,
    decision_readiness: Any = None,
    decision_gate: Optional[Dict[str, Any]] = None,
    synthesis: Optional[Dict[str, Any]] = None,
    governance: Optional[Dict[str, Any]] = None,
    domain: str = "shared",
    case_id: Optional[str] = None,
    case_version: int = 1,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> InstitutionalInvestmentCase:
    """Assemble existing analytical outputs without recomputing them."""
    gate = decision_gate or {}
    evidence_status = evidence_summary or {}
    synthesis_output = synthesis or {}
    governance_output = dict(governance or {})
    now = _now_iso()

    # Preserve the existing authority boundary even if a caller supplies unsafe values.
    governance_output.update({
        "human_decision_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    })

    return InstitutionalInvestmentCase(
        case_id=case_id or f"CASE-{uuid4().hex}",
        case_version=case_version,
        created_at=created_at or now,
        updated_at=updated_at or now,
        status=_status_from_outputs(evidence_status, gate, synthesis_output),
        investment_question=question,
        domain=domain,
        opportunity=opportunity,
        identity=identity,
        evidence=evidence or [],
        claims=claims or [],
        thesis=thesis or {},
        assumptions=assumptions or [],
        calculations=calculations,
        valuation=valuation,
        scenarios=scenarios,
        risk=risk,
        perspectives=perspectives,
        conflicts=conflicts,
        contrarian_review=contrarian_review,
        decision_readiness=decision_readiness if decision_readiness is not None else gate,
        decision_options=[
            "INVESTIGATE",
            "NO_GO",
            "NO_DEAL",
            "INSUFFICIENT_EVIDENCE",
            "HOLD",
            "CONDITIONAL_GO",
            "READY_FOR_HUMAN_AUTHORITY",
        ],
        governance=governance_output,
    )
