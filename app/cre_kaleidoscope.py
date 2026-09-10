"""CRE adapter for the existing Computational Kaleidoscope."""
from dataclasses import dataclass, field
from typing import Any, Sequence

CRE_PERSPECTIVES = (
    "underwriter", "investor", "quant", "researcher", "macro", "systems", "contrarian", "risk"
)


@dataclass(frozen=True)
class PerspectiveAssessment:
    opportunity_id: str
    perspective_id: str
    thesis: str
    supporting_evidence: Sequence[str] = field(default_factory=tuple)
    contradictory_evidence: Sequence[str] = field(default_factory=tuple)
    assumptions: Sequence[str] = field(default_factory=tuple)
    confidence: float | None = None
    time_horizon: str | None = None
    risks: Sequence[str] = field(default_factory=tuple)
    uncertainty: Sequence[str] = field(default_factory=tuple)
    invalidation_conditions: Sequence[str] = field(default_factory=tuple)
    unanswered_questions: Sequence[str] = field(default_factory=tuple)
    recommendation: str | None = None
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    economic_metrics: dict[str, float | None] = field(default_factory=dict)
    economic_claims: Sequence[str] = field(default_factory=tuple)
    audit_metadata: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.perspective_id not in CRE_PERSPECTIVES:
            raise ValueError(f"unknown CRE perspective: {self.perspective_id}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


def empty_assessments(opportunity_id: str) -> tuple[PerspectiveAssessment, ...]:
    """Create inspectable placeholders; no perspective is silently invented."""
    return tuple(PerspectiveAssessment(opportunity_id, perspective, "Assessment not yet produced.") for perspective in CRE_PERSPECTIVES)
