"""CRE decision gate that preserves uncertainty and human authority."""
from dataclasses import dataclass, field
from typing import Any, Sequence

from .cre_underwriting import UnderwritingDecision, UnderwritingResult, CREFinancialResult


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


@dataclass(frozen=True)
class CREDecisionCriteria:
    """Optional research criteria. None means no universal threshold is assumed."""
    min_dscr: float | None = None
    min_cash_on_cash: float | None = None
    min_irr: float | None = None
    min_equity_multiple: float | None = None
    max_ltv: float | None = None


def evaluate_financial_decision(
    financial: CREFinancialResult,
    criteria: CREDecisionCriteria,
    supplied_ltv: float | None = None,
) -> CREDecisionRecord:
    """Apply only explicitly configured economic criteria; never authorizes execution."""
    if financial.status != "CALCULATED":
        return CREDecisionRecord(
            state=UnderwritingDecision.INSUFFICIENT_EVIDENCE,
            rationale="Financial model is incomplete: " + ", ".join(financial.missing_inputs),
            evidence_ids=financial.evidence_ids,
        )
    failures: list[str] = []
    if criteria.min_dscr is not None and (financial.dscr is None or financial.dscr < criteria.min_dscr):
        failures.append(f"DSCR {financial.dscr if financial.dscr is not None else 'UNKNOWN'} is below configured minimum {criteria.min_dscr:.2f}x.")
    if criteria.min_cash_on_cash is not None and (financial.cash_on_cash is None or financial.cash_on_cash < criteria.min_cash_on_cash):
        failures.append("Cash-on-cash return is below the configured minimum.")
    if criteria.min_irr is not None and (financial.irr is None or financial.irr < criteria.min_irr):
        failures.append("IRR is below the configured minimum.")
    if criteria.min_equity_multiple is not None and (financial.equity_multiple is None or financial.equity_multiple < criteria.min_equity_multiple):
        failures.append("Equity multiple is below the configured minimum.")
    if criteria.max_ltv is not None and supplied_ltv is not None and supplied_ltv > criteria.max_ltv:
        failures.append(f"LTV {supplied_ltv:.2%} exceeds configured maximum {criteria.max_ltv:.2%}.")
    if failures:
        return CREDecisionRecord(
            state=UnderwritingDecision.NO_DEAL,
            rationale=" ".join(failures),
            evidence_ids=financial.evidence_ids,
        )
    return CREDecisionRecord(
        state=UnderwritingDecision.WATCH,
        rationale="Financial model meets all explicitly configured research criteria; further diligence and human decision remain required.",
        evidence_ids=financial.evidence_ids,
    )


def build_decision_record(underwriting: UnderwritingResult, unresolved_questions: Sequence[str] = ()) -> CREDecisionRecord:
    """Translate underwriting state into an auditable research disposition."""
    return CREDecisionRecord(
        state=underwriting.decision,
        rationale=" ".join(underwriting.reasons) or "No conclusion available.",
        unresolved_questions=tuple(unresolved_questions),
        evidence_ids=tuple(underwriting.evidence_ids),
    )
