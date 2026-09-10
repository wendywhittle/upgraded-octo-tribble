"""Institutional CRE intelligence primitives."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class CREStage(str, Enum):
    OPPORTUNITY = "OPPORTUNITY"
    SCREENING = "SCREENING"
    UNDERWRITING = "UNDERWRITING"
    DUE_DILIGENCE = "DUE DILIGENCE"
    SCENARIO_ANALYSIS = "SCENARIO ANALYSIS"
    CAPITAL_STRUCTURE = "CAPITAL STRUCTURE"
    VALUE_CREATION = "VALUE CREATION"
    INVESTMENT_COMMITTEE = "INVESTMENT COMMITTEE"
    CAPITAL = "CAPITAL"
    ASSET = "ASSET"
    OPERATE_IMPROVE = "OPERATE / IMPROVE"
    OBSERVE_OUTCOME = "OBSERVE OUTCOME"
    EPISTEMIC_MEMORY = "EPISTEMIC MEMORY"


class CREDecision(str, Enum):
    ACT = "ACT"
    WATCH = "WATCH"
    REJECT = "REJECT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"
    NO_DEAL = "NO DEAL"


@dataclass(frozen=True)
class CREOpportunity:
    opportunity_id: str
    asset_type: str
    market: str
    asking_price: float | None = None
    noi: float | None = None
    occupancy: float | None = None
    evidence_ids: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScreeningResult:
    decision: CREDecision
    reasons: Sequence[str] = field(default_factory=tuple)
    missing_evidence: Sequence[str] = field(default_factory=tuple)


def screen(opportunity: CREOpportunity) -> ScreeningResult:
    """Conservative first-pass screen. It never authorizes a deal."""
    missing: list[str] = []
    if not opportunity.market.strip():
        missing.append("market")
    if opportunity.asking_price is None or opportunity.asking_price <= 0:
        missing.append("asking_price")
    if opportunity.noi is None or opportunity.noi < 0:
        missing.append("noi")
    if opportunity.occupancy is None or not 0 <= opportunity.occupancy <= 1:
        missing.append("occupancy")

    if missing:
        return ScreeningResult(
            decision=CREDecision.INSUFFICIENT_EVIDENCE,
            reasons=("Critical screening inputs are missing or invalid.",),
            missing_evidence=tuple(missing),
        )

    assert opportunity.asking_price is not None
    assert opportunity.noi is not None
    cap_rate = opportunity.noi / opportunity.asking_price
    reasons = [f"Indicative going-in cap rate: {cap_rate:.2%}"]
    if opportunity.occupancy < 0.75:
        reasons.append("Occupancy requires additional diligence.")
    reasons.append("Screening is not investment approval.")
    return ScreeningResult(decision=CREDecision.WATCH, reasons=tuple(reasons))
