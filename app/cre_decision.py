"""CRE decision gate that preserves uncertainty and human authority."""
from dataclasses import dataclass, field
from typing import Sequence

from .cre_underwriting import UnderwritingDecision, UnderwritingResult


@dataclass(frozen=True)
class CREDecisionRecord:
    state: UnderwritingDecision
    rationale: str
    unresolved_questions: Sequence[str] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    human_decision_required: bool = True
    autonomous_execution: bool = False

    def __post_init__(self) -> None:
        if not self.human_decision_required:
            raise ValueError("human decision authority must remain explicit")
        if self.autonomous_execution:
            raise ValueError("CRE decision records cannot authorize autonomous execution")


def build_decision_record(
    underwriting: UnderwritingResult,
    unresolved_questions: Sequence[str] = (),
) -> CREDecisionRecord:
    """Translate underwriting state into an auditable research disposition."""
    return CREDecisionRecord(
        state=underwriting.decision,
        rationale=" ".join(underwriting.reasons) or "No conclusion available.",
        unresolved_questions=tuple(unresolved_questions),
        evidence_ids=tuple(underwriting.evidence_ids),
    )
