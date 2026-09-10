"""Deterministic CRE perspectives over one shared context and economic model.

These are structured reasoning lenses, not autonomous agents. They do not execute,
select a portfolio action, or override human authority.
"""
from dataclasses import asdict
from typing import Callable, Any

from .cre_context import CREOpportunityContext
from .cre_kaleidoscope import CRE_PERSPECTIVES, PerspectiveAssessment


def _common(ctx: CREOpportunityContext, financial_result: Any | None = None) -> dict:
    labels = list(ctx.assumption_labels())
    if financial_result is not None:
        for name in ("going_in_cap_rate", "annual_debt_service", "dscr", "debt_yield", "cash_on_cash", "exit_value", "net_sale_proceeds", "equity_multiple", "irr"):
            value = getattr(financial_result, name, None)
            if value is not None:
                labels.append(f"{name}={value}")
    return {
        "opportunity_id": ctx.opportunity_id,
        "supporting_evidence": tuple(ctx.evidence),
        "contradictory_evidence": tuple(ctx.contradictory_evidence),
        "evidence_ids": tuple(ctx.evidence),
        "assumptions": tuple(labels),
        "uncertainty": tuple(ctx.uncertainty) + tuple(ctx.evidence_quality_flags()),
    }


def _assessment(ctx: CREOpportunityContext, perspective: str, thesis: str, risks: tuple[str, ...], questions: tuple[str, ...], invalidations: tuple[str, ...], recommendation: str = "WATCH", financial_result: Any | None = None) -> PerspectiveAssessment:
    data = _common(ctx, financial_result)
    return PerspectiveAssessment(
        perspective_id=perspective,
        thesis=thesis,
        risks=risks,
        unanswered_questions=questions,
        invalidation_conditions=invalidations,
        recommendation=recommendation,
        confidence=None if ctx.missing_required() else 0.5,
        time_horizon="investment horizon",
        audit_metadata=("deterministic_structured_lens", "shared_economic_model", "human_authority_required"),
        **data,
    )


def _underwriter(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    missing = ctx.missing_required()
    if model is not None and getattr(model, "missing_inputs", ()):
        missing = tuple(dict.fromkeys((*missing, *model.missing_inputs)))
    if missing:
        thesis = "Underwriting cannot be responsibly completed until required inputs are verified."
        recommendation = "INSUFFICIENT EVIDENCE"
    else:
        cap = getattr(model, "going_in_cap_rate", None)
        thesis = f"First-pass property economics calculate a {cap:.2%} going-in cap rate and require evidence review before approval." if cap is not None else "The opportunity is underwritable at first-pass level, subject to assumption and evidence review."
        recommendation = "WATCH"
    return _assessment(ctx, "underwriter", thesis, ("NOI quality", "expense and leasing assumptions"), tuple(missing) or ("Verify normalized NOI and lease terms",), ("Material NOI adjustment", "Unverified lease or expense assumption"), recommendation, model)


def _investor(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    coc = getattr(model, "cash_on_cash", None)
    thesis = "Investment attractiveness depends on risk-adjusted return and sufficient margin of safety, not headline yield alone."
    if coc is not None:
        thesis += f" Modeled first-year cash-on-cash is {coc:.2%}."
    return _assessment(ctx, "investor", thesis, ("opportunity cost", "capital preservation"), ("What alternative use of capital offers better risk-adjusted value?", "What downside remains after financing?"), ("Downside exceeds acceptable margin of safety",), financial_result=model)


def _quant(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    thesis = "Quantitative judgment should be expressed through measurable assumptions, distributions, sensitivity, and uncertainty rather than a single point estimate."
    irr = getattr(model, "irr", None)
    if irr is not None:
        thesis += f" The deterministic base model produces an IRR of {irr:.2%} before stochastic scenario analysis."
    return _assessment(ctx, "quant", thesis, ("model risk", "parameter sensitivity"), ("Which variables dominate outcome variance?",), ("Distribution remains unacceptable under reasonable assumptions",), financial_result=model)


def _researcher(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    quality = ctx.evidence_quality_flags()
    thesis = "Evidence quality requires additional verification." if quality or not ctx.evidence else "Available evidence can support structured review, subject to source verification."
    return _assessment(ctx, "researcher", thesis, ("stale or incomplete evidence", "contradictory claims"), ("Which primary sources remain unverified?",), ("Material claim cannot be independently corroborated",), "INSUFFICIENT EVIDENCE" if quality or not ctx.evidence else "WATCH", model)


def _macro(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    rate = ctx.interest_rate
    thesis = "The opportunity must be tested against the relevant rate, demand, employment, and property-market regime rather than a static base case."
    if rate is not None:
        thesis += f" Current underwriting explicitly carries a {rate:.2%} financing-rate input."
    return _assessment(ctx, "macro", thesis, ("rate regime", "demand regime"), ("What macro regime is underwriting implicitly assuming?",), ("Rates or demand move outside underwriting tolerance",), financial_result=model)


def _systems(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    return _assessment(ctx, "systems", "The thesis is a dependency network involving operations, leasing, financing, capital expenditures, and exit conditions.", ("dependency chains", "operational fragility"), ("Which dependency can fail first and propagate?",), ("A critical dependency lacks a credible fallback",), financial_result=model)


def _contrarian(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    exit = getattr(model, "exit_value", None)
    thesis = "The strongest useful case is that the apparent opportunity is mispriced because one or more central assumptions fail."
    if exit is not None:
        thesis += f" The modeled exit value is {exit:,.0f}, making exit assumptions a material challenge point."
    return _assessment(ctx, "contrarian", thesis, ("thesis failure", "permanent capital loss"), ("What is the strongest evidence against the deal?", "Which assumption is most fragile?"), ("A central thesis assumption is falsified",), "WATCH", model)


def _risk(ctx: CREOpportunityContext, model: Any | None) -> PerspectiveAssessment:
    dscr = getattr(model, "dscr", None)
    thesis = "Capital preservation requires explicit downside, leverage, liquidity, concentration, and tail-risk analysis before deployment."
    if dscr is not None:
        thesis += f" Base debt-service coverage is {dscr:.2f}x under supplied financing assumptions."
    return _assessment(ctx, "risk", thesis, ("leverage", "liquidity", "tail risk"), ("What is the plausible permanent loss path?",), ("Downside cannot be contained within the investment mandate",), financial_result=model)


_PERSPECTIVE_BUILDERS: dict[str, Callable[[CREOpportunityContext, Any | None], PerspectiveAssessment]] = {
    "underwriter": _underwriter, "investor": _investor, "quant": _quant, "researcher": _researcher,
    "macro": _macro, "systems": _systems, "contrarian": _contrarian, "risk": _risk,
}


def assess_cre_opportunity(ctx: CREOpportunityContext, financial_result: Any | None = None) -> tuple[PerspectiveAssessment, ...]:
    """Run all eight lenses over exactly the same context and, when available, model."""
    return tuple(_PERSPECTIVE_BUILDERS[name](ctx, financial_result) for name in CRE_PERSPECTIVES)


def assessments_as_dicts(ctx: CREOpportunityContext, financial_result: Any | None = None) -> list[dict]:
    return [asdict(item) for item in assess_cre_opportunity(ctx, financial_result)]
