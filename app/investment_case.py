"""Structured Investment Case boundary for research-only convergence.

The Investment Case is a structured research artifact immediately before the
human decision gate. It does not authorize, execute, allocate, or mutate capital.
Missing analytical components are represented as explicit gaps rather than inferred.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.capital_stack import CapitalStack, LenderEvidence
from app.cre_evidence import CREEvidence
from app.opportunity import CREOpportunityDeal
from app.underwriting import CREUnderwritingProForma


CaseRecommendation = Literal[
    "NO_DATA",
    "NO_GO",
    "HOLD",
    "CONDITIONAL_GO",
    "INVESTIGATE",
]


class InvestmentCaseRef(BaseModel):
    """Typed reference to an upstream analytical artifact."""

    model_config = ConfigDict(frozen=True)

    ref_type: str = Field(min_length=1)
    ref_id: str = Field(min_length=1)
    source: str = Field(min_length=1)


class HumanDecisionGate(BaseModel):
    """Gate metadata only. It deliberately contains no authorization action."""

    model_config = ConfigDict(frozen=True)

    required: bool = True
    status: Literal["pending"] = "pending"
    authorization_record_id: Optional[str] = None
    authorized: bool = False


class StructuredInvestmentCase(BaseModel):
    """Convergence artifact assembled from existing analytical outputs."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(min_length=1)
    created_at: datetime
    question: str = Field(min_length=1)
    opportunity: Dict[str, Any] = Field(default_factory=dict)
    opportunity_deal: Optional[CREOpportunityDeal] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    cre_evidence: List[CREEvidence] = Field(default_factory=list)
    evidence_refs: List[InvestmentCaseRef] = Field(default_factory=list)
    independent_reasoning: List[Dict[str, Any]] = Field(default_factory=list)
    claims_and_interpretations: List[Dict[str, Any]] = Field(default_factory=list)
    validated_assumptions: List[str] = Field(default_factory=list)
    pro_forma: Optional[CREUnderwritingProForma] = None
    calculations: List[Dict[str, Any]] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    simulation: Dict[str, Any] = Field(default_factory=dict)
    contrarian_review: Dict[str, Any] = Field(default_factory=dict)
    capital_stack: Optional[CapitalStack] = None
    lender_evidence: List[LenderEvidence] = Field(default_factory=list)
    synthesis: Dict[str, Any] = Field(default_factory=dict)
    recommendation: CaseRecommendation
    recommendation_basis: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    human_decision_gate: HumanDecisionGate = Field(default_factory=HumanDecisionGate)
    authority: Literal["none"] = "none"
    execution_capability: Literal[False] = False
    portfolio_mutation: Literal[False] = False


def _case_id(question: str, created_at: datetime) -> str:
    """Create a case identifier without introducing authority."""
    stamp = created_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"investment-case:{stamp}:{abs(hash(question)) % 10**8:08d}"


def build_structured_investment_case(
    *,
    question: str,
    evidence: Dict[str, Any],
    agents: List[Dict[str, Any]],
    simulation: Dict[str, Any],
    skeptic: Dict[str, Any],
    synthesis: Dict[str, Any],
    meta_intelligence: Dict[str, Any] | None = None,
    opportunity_deal: CREOpportunityDeal | None = None,
    cre_evidence: List[CREEvidence] | None = None,
    underwriting: CREUnderwritingProForma | None = None,
    capital_stack: CapitalStack | None = None,
    lender_evidence: List[LenderEvidence] | None = None,
    financing_assumptions: List[str] | None = None,
    financing_risks: List[str] | None = None,
    created_at: datetime | None = None,
) -> StructuredInvestmentCase:
    """Converge existing outputs without inventing missing CRE components."""
    now = created_at or datetime.now(timezone.utc)
    lender_records = list(lender_evidence or [])
    cre_evidence_records = list(cre_evidence or [])
    evidence_refs = [
        InvestmentCaseRef(ref_type="evidence", ref_id=str(item["evidence_id"]), source=str(item.get("source", "unknown")))
        for item in evidence.get("items", [])
        if item.get("evidence_id")
    ]
    assumptions = [
        assumption
        for agent in agents
        for assumption in agent.get("assumptions", [])
        if isinstance(assumption, str)
    ]
    assumptions.extend(item for item in (financing_assumptions or []) if isinstance(item, str))
    scenarios = list(simulation.get("scenarios", []))
    recommendation = {
        "NO_DATA": "NO_DATA",
        "NO_GO": "NO_GO",
        "HOLD": "HOLD",
        "CONDITIONAL GO": "CONDITIONAL_GO",
        "CONDITIONAL_GO": "CONDITIONAL_GO",
        "INVESTIGATE": "INVESTIGATE",
    }.get(str(synthesis.get("verdict")), "INVESTIGATE")
    if recommendation != "NO_GO" and skeptic.get("recommendation") == "hold":
        recommendation = "HOLD"

    gaps: List[str] = []
    if not evidence_refs and not cre_evidence_records:
        gaps.append("No usable evidence references were supplied to the Investment Case.")
    if not any(agent.get("assumptions") for agent in agents):
        gaps.append("No explicit agent assumptions were available.")
    if opportunity_deal is None:
        gaps.append("Canonical CRE opportunity / deal representation is not yet supplied.")
    if underwriting is None:
        gaps.append("CRE underwriting / property-level pro forma is not yet supplied.")
    if capital_stack is None:
        gaps.append("Capital stack is not present in the inspected architecture.")
    if not lender_records:
        gaps.append("Lender evidence is not present in the inspected architecture.")
    if financing_risks:
        gaps.extend(f"Financing risk: {risk}" for risk in financing_risks)

    basis = list(synthesis.get("unresolved_questions", []))
    if skeptic.get("challenges"):
        basis.extend(skeptic["challenges"])
    if meta_intelligence:
        basis.append("Meta-Intelligence evaluation is informational and does not authorize action.")

    return StructuredInvestmentCase(
        case_id=_case_id(question, now),
        created_at=now,
        question=question,
        opportunity={"question": question},
        opportunity_deal=opportunity_deal,
        evidence=evidence,
        cre_evidence=cre_evidence_records,
        evidence_refs=evidence_refs,
        independent_reasoning=agents,
        claims_and_interpretations=[
            {"type": "synthesis", "content": synthesis},
            {"type": "meta_intelligence", "content": meta_intelligence or {}},
        ],
        validated_assumptions=list(dict.fromkeys(assumptions)),
        pro_forma=underwriting,
        calculations=[],
        scenarios=scenarios,
        simulation=simulation,
        contrarian_review=skeptic,
        capital_stack=capital_stack,
        lender_evidence=lender_records,
        synthesis=synthesis,
        recommendation=recommendation,
        recommendation_basis=list(dict.fromkeys(basis)),
        gaps=list(dict.fromkeys(gaps)),
    )
