"""CRE decision gate that preserves uncertainty and human authority."""
from dataclasses import dataclass, field
from typing import Any, Sequence

from .cre_underwriting import UnderwritingDecision, UnderwritingResult, CREFinancialResult


@dataclass(frozen=True)
class CREDecisionRecord:
    state: UnderwritingDecision
    rationale: str
    criteria_satisfied: Sequence[str] = field(default_factory=tuple)
    criteria_failed: Sequence[str] = field(default_factory=tuple)
    unresolved_questions: Sequence[str] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    human_decision_required: bool = True
    autonomous_execution: bool = False

    def __post_init__(self) -> None:
        if self.state is UnderwritingDecision.REJECT:
            raise ValueError("REJECT is not a supported CRE decision state")
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
            unresolved_questions=tuple(financial.missing_inputs),
            evidence_ids=financial.evidence_ids,
        )
    failures: list[str] = []
    satisfied: list[str] = []
    if criteria.min_dscr is not None:
        if financial.dscr is None or financial.dscr < criteria.min_dscr:
            failures.append(f"DSCR {financial.dscr if financial.dscr is not None else 'UNKNOWN'} is below configured minimum {criteria.min_dscr:.2f}x.")
        else:
            satisfied.append(f"DSCR >= {criteria.min_dscr:.2f}x")
    if criteria.min_cash_on_cash is not None:
        if financial.cash_on_cash is None or financial.cash_on_cash < criteria.min_cash_on_cash:
            failures.append("Cash-on-cash return is below the configured minimum.")
        else:
            satisfied.append(f"Cash-on-cash >= {criteria.min_cash_on_cash:.2%}")
    if criteria.min_irr is not None:
        if financial.irr is None or financial.irr < criteria.min_irr:
            failures.append("IRR is below the configured minimum.")
        else:
            satisfied.append(f"IRR >= {criteria.min_irr:.2%}")
    if criteria.min_equity_multiple is not None:
        if financial.equity_multiple is None or financial.equity_multiple < criteria.min_equity_multiple:
            failures.append("Equity multiple is below the configured minimum.")
        else:
            satisfied.append(f"Equity multiple >= {criteria.min_equity_multiple:.2f}x")
    if criteria.max_ltv is not None:
        if supplied_ltv is None:
            failures.append("LTV is UNKNOWN; configured maximum LTV cannot be verified.")
        elif supplied_ltv > criteria.max_ltv:
            failures.append(f"LTV {supplied_ltv:.2%} exceeds configured maximum {criteria.max_ltv:.2%}.")
        else:
            satisfied.append(f"LTV <= {criteria.max_ltv:.2%}")
    if failures:
        return CREDecisionRecord(
            state=UnderwritingDecision.NO_DEAL,
            rationale=" ".join(failures),
            criteria_satisfied=tuple(satisfied),
            criteria_failed=tuple(failures),
            evidence_ids=financial.evidence_ids,
        )
    configured = (
        criteria.min_dscr is not None
        or criteria.min_cash_on_cash is not None
        or criteria.min_irr is not None
        or criteria.min_equity_multiple is not None
        or criteria.max_ltv is not None
    )
    if configured:
        return CREDecisionRecord(
            state=UnderwritingDecision.ACT,
            rationale="Financial model meets all explicitly configured research criteria; this is a recommendation only and still requires human authorization.",
            criteria_satisfied=tuple(satisfied),
            evidence_ids=financial.evidence_ids,
        )
    return CREDecisionRecord(
        state=UnderwritingDecision.WATCH,
        rationale="Financial model is calculable but no explicit decision criteria were configured; further diligence and human decision remain required.",
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
