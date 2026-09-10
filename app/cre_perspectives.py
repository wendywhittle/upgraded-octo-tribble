"""Deterministic first-pass CRE perspectives over one shared context.

These are structured reasoning lenses, not autonomous agents. They do not execute,
select a portfolio action, or override human authority.
"""
from dataclasses import asdict
from typing import Callable

from .cre_context import CREOpportunityContext
from .cre_kaleidoscope import CRE_PERSPECTIVES, PerspectiveAssessment


def _common(ctx: CREOpportunityContext) -> dict:
    return {
        "opportunity_id": ctx.opportunity_id,
        "supporting_evidence": tuple(ctx.evidence),
        "contradictory_evidence": tuple(ctx.contradictory_evidence),
        "evidence_ids": tuple(ctx.evidence),
        "assumptions": ctx.assumption_labels(),
        "uncertainty": tuple(ctx.uncertainty) + tuple(ctx.evidence_quality_flags()),
    }


def _assessment(ctx: CREOpportunityContext, perspective: str, thesis: str, risks: tuple[str, ...], questions: tuple[str, ...], invalidations: tuple[str, ...], recommendation: str = "WATCH") -> PerspectiveAssessment:
    data = _common(ctx)
    return PerspectiveAssessment(
        perspective_id=perspective,
        thesis=thesis,
        risks=risks,
        unanswered_questions=questions,
        invalidation_conditions=invalidations,
        recommendation=recommendation,
        confidence=None if ctx.missing_required() else 0.5,
        time_horizon="investment horizon",
        audit_metadata=("deterministic_structured_lens", "human_authority_required"),
        **data,
    )


def _underwriter(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    missing = ctx.missing_required()
    thesis = "Underwriting cannot be responsibly completed until required inputs are verified." if missing else "The opportunity is underwritable at first-pass level, subject to assumption and evidence review."
    return _assessment(ctx, "underwriter", thesis, ("NOI quality", "expense and leasing assumptions"), tuple(missing) or ("Verify normalized NOI and lease terms",), ("Material NOI adjustment", "Unverified lease or expense assumption"), "INSUFFICIENT EVIDENCE" if missing else "WATCH")


def _investor(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "investor", "Investment attractiveness depends on risk-adjusted return and sufficient margin of safety, not headline yield alone.", ("opportunity cost", "capital preservation"), ("What alternative use of capital offers better risk-adjusted value?",), ("Downside exceeds acceptable margin of safety",))


def _quant(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "quant", "Quantitative judgment should be expressed through measurable assumptions, distributions, sensitivity, and uncertainty rather than a single point estimate.", ("model risk", "parameter sensitivity"), ("Which variables dominate outcome variance?",), ("Distribution remains unacceptable under reasonable assumptions",))


def _researcher(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    quality = ctx.evidence_quality_flags()
    thesis = "Evidence quality requires additional verification." if quality or not ctx.evidence else "Available evidence can support structured review, subject to source verification."
    return _assessment(ctx, "researcher", thesis, ("stale or incomplete evidence", "contradictory claims"), ("Which primary sources remain unverified?",), ("Material claim cannot be independently corroborated",), "INSUFFICIENT EVIDENCE" if quality or not ctx.evidence else "WATCH")


def _macro(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "macro", "The opportunity must be tested against the relevant rate, demand, employment, and property-market regime rather than a static base case.", ("rate regime", "demand regime"), ("What macro regime is underwriting implicitly assuming?",), ("Rates or demand move outside underwriting tolerance",))


def _systems(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "systems", "The thesis is a dependency network involving operations, leasing, financing, capital expenditures, and exit conditions.", ("dependency chains", "operational fragility"), ("Which dependency can fail first and propagate?",), ("A critical dependency lacks a credible fallback",))


def _contrarian(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "contrarian", "The strongest useful case is that the apparent opportunity is mispriced because one or more central assumptions fail.", ("thesis failure", "permanent capital loss"), ("What is the strongest evidence against the deal?", "Which assumption is most fragile?"), ("A central thesis assumption is falsified"), "WATCH")


def _risk(ctx: CREOpportunityContext) -> PerspectiveAssessment:
    return _assessment(ctx, "risk", "Capital preservation requires explicit downside, leverage, liquidity, concentration, and tail-risk analysis before deployment.", ("leverage", "liquidity", "tail risk"), ("What is the plausible permanent loss path?",), ("Downside cannot be contained within the investment mandate",))


_PERSPECTIVE_BUILDERS: dict[str, Callable[[CREOpportunityContext], PerspectiveAssessment]] = {
    "underwriter": _underwriter, "investor": _investor, "quant": _quant, "researcher": _researcher,
    "macro": _macro, "systems": _systems, "contrarian": _contrarian, "risk": _risk,
}


def assess_cre_opportunity(ctx: CREOpportunityContext) -> tuple[PerspectiveAssessment, ...]:
    """Run all eight lenses over exactly the same structured opportunity context."""
    return tuple(_PERSPECTIVE_BUILDERS[name](ctx) for name in CRE_PERSPECTIVES)


def assessments_as_dicts(ctx: CREOpportunityContext) -> list[dict]:
    return [asdict(item) for item in assess_cre_opportunity(ctx)]
