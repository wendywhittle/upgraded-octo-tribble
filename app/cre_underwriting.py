"""Structured, auditable CRE underwriting primitives."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class UnderwritingDecision(str, Enum):
    ACT = "ACT"
    WATCH = "WATCH"
    REJECT = "REJECT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"
    NO_DEAL = "NO DEAL"


@dataclass(frozen=True)
class Property:
    property_id: str
    asset_type: str
    market: str
    rentable_area: float | None = None
    occupancy: float | None = None
    year_built: int | None = None


@dataclass(frozen=True)
class Assumption:
    name: str
    value: float | str
    unit: str
    source: str | None = None
    evidence_id: str | None = None
    confidence: float | None = None
    invalidation_condition: str | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("assumption confidence must be between 0 and 1")
        if self.value is None:
            raise ValueError("assumption value cannot be None")


@dataclass(frozen=True)
class UnderwritingInputs:
    opportunity_id: str
    property: Property
    purchase_price: float | None
    annual_noi: float | None
    assumptions: Sequence[Assumption] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    contradictory_evidence: Sequence[str] = field(default_factory=tuple)
    uncertainty_notes: Sequence[str] = field(default_factory=tuple)
    no_deal_reasons: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class UnderwritingResult:
    decision: UnderwritingDecision
    going_in_cap_rate: float | None
    reasons: Sequence[str] = field(default_factory=tuple)
    missing_inputs: Sequence[str] = field(default_factory=tuple)
    fragile_assumptions: Sequence[str] = field(default_factory=tuple)
    invalidation_conditions: Sequence[str] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)


def underwrite(inputs: UnderwritingInputs) -> UnderwritingResult:
    """Perform deterministic first-pass underwriting without inventing inputs."""
    missing: list[str] = []
    if not inputs.opportunity_id.strip():
        missing.append("opportunity_id")
    if not inputs.property.asset_type.strip():
        missing.append("property.asset_type")
    if not inputs.property.market.strip():
        missing.append("property.market")
    if inputs.purchase_price is None or inputs.purchase_price <= 0:
        missing.append("purchase_price")
    if inputs.annual_noi is None or inputs.annual_noi < 0:
        missing.append("annual_noi")

    if missing:
        return UnderwritingResult(
            decision=UnderwritingDecision.INSUFFICIENT_EVIDENCE,
            going_in_cap_rate=None,
            reasons=("Required underwriting inputs are missing or invalid.",),
            missing_inputs=tuple(missing),
            evidence_ids=tuple(inputs.evidence_ids),
        )

    assert inputs.purchase_price is not None
    assert inputs.annual_noi is not None
    cap_rate = inputs.annual_noi / inputs.purchase_price
    fragile = tuple(a.name for a in inputs.assumptions if a.confidence is not None and a.confidence < 0.6)
    invalidations = tuple(a.invalidation_condition for a in inputs.assumptions if a.invalidation_condition)
    reasons = [f"Going-in cap rate: {cap_rate:.2%}"]
    if inputs.contradictory_evidence:
        reasons.append("Contradictory evidence is present and requires review.")
    if inputs.uncertainty_notes:
        reasons.append("Material uncertainty has been recorded.")
    if fragile:
        reasons.append("One or more assumptions have low recorded confidence.")
    if inputs.no_deal_reasons:
        reasons.extend(inputs.no_deal_reasons)
        return UnderwritingResult(
            decision=UnderwritingDecision.NO_DEAL,
            going_in_cap_rate=cap_rate,
            reasons=tuple(reasons),
            fragile_assumptions=fragile,
            invalidation_conditions=invalidations,
            evidence_ids=tuple(inputs.evidence_ids),
        )

    return UnderwritingResult(
        decision=UnderwritingDecision.WATCH,
        going_in_cap_rate=cap_rate,
        reasons=tuple(reasons),
        fragile_assumptions=fragile,
        invalidation_conditions=invalidations,
        evidence_ids=tuple(inputs.evidence_ids),
    )
