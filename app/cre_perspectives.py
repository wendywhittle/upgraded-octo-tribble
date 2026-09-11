"""Deterministic CRE perspectives over one shared economic model.

These are structured reasoning lenses, not autonomous agents. They do not execute,
select a portfolio action, or override human authority.
"""
from dataclasses import asdict
from typing import Callable, Any

from .cre_context import CREOpportunityContext
from .cre_kaleidoscope import CRE_PERSPECTIVES, PerspectiveAssessment
from .cre_underwriting import CREFinancialInputs, underwrite_financial_model


def _metrics(model: Any | None) -> dict[str, float | None]:
    if model is None:
        return {}
    names = ("going_in_cap_rate", "annual_debt_service", "dscr", "debt_yield", "cash_on_cash", "exit_value", "net_sale_proceeds", "equity_multiple", "irr", "break_even_occupancy", "break_even_exit_cap", "max_purchase_price_at_target_cap", "max_loan_at_target_dscr")
    return {name: getattr(model, name, None) for name in names}


def _common(ctx: CREOpportunityContext, financial_result: Any | None = None) -> dict:
    labels = list(ctx.assumption_labels())
    metrics = _metrics(financial_result)
    labels.extend(f"{name}={value}" for name, value in metrics.items() if value is not None)
    return {"opportunity_id": ctx.opportunity_id,"supporting_evidence": tuple(ctx.evidence),"contradictory_evidence": tuple(ctx.contradictory_evidence),"evidence_ids": tuple(ctx.evidence),"assumptions": tuple(labels),"uncertainty": tuple(ctx.uncertainty) + tuple(ctx.evidence_quality_flags()),"economic_metrics": metrics}


def _assessment(ctx: CREOpportunityContext, perspective: str, thesis: str, risks: tuple[str, ...], questions: tuple[str, ...], invalidations: tuple[str, ...], recommendation: str = "WATCH", financial_result: Any | None = None, claims: tuple[str, ...] = ()) -> PerspectiveAssessment:
    data = _common(ctx, financial_result)
    return PerspectiveAssessment(perspective_id=perspective, thesis=thesis, risks=risks, unanswered_questions=questions, invalidation_conditions=invalidations, recommendation=recommendation, confidence=None if ctx.missing_required() else 0.5, time_horizon="investment horizon", economic_claims=claims, audit_metadata=("deterministic_structured_lens", "shared_economic_model", "human_authority_required"), **data)


def _underwriter(ctx, model):
    missing = ctx.missing_required()
    if model is not None and getattr(model, "missing_inputs", ()): missing = tuple(dict.fromkeys((*missing, *model.missing_inputs)))
    if missing: return _assessment(ctx, "underwriter", "Underwriting cannot be responsibly completed until required inputs are verified.", ("incomplete economics",), tuple(missing), ("Material NOI or financing input changes",), "INSUFFICIENT EVIDENCE", model)
    cap, dscr = model.going_in_cap_rate, model.dscr; claims = tuple(x for x in (f"Going-in cap rate is {cap:.2%}." if cap is not None else None, f"Base DSCR is {dscr:.2f}x." if dscr is not None else None) if x)
    return _assessment(ctx, "underwriter", "Property-level economics are calculable, subject to normalized NOI, lease and financing verification.", ("NOI quality", "lease and expense assumptions"), ("Verify normalized NOI and lease terms",), ("Material NOI adjustment", "Unverified lease or expense assumption"), "WATCH", model, claims)


def _investor(ctx, model):
    coc, irr_value, net_sale = getattr(model, "cash_on_cash", None), getattr(model, "irr", None), getattr(model, "net_sale_proceeds", None); claims = tuple(x for x in (f"First-year cash-on-cash is {coc:.2%}." if coc is not None else None, f"Modeled IRR is {irr_value:.2%}." if irr_value is not None else None, f"Net sale proceeds are {net_sale:,.0f}." if net_sale is not None else None) if x)
    return _assessment(ctx, "investor", "Return must be judged against downside and margin of safety, not headline yield alone.", ("opportunity cost", "capital preservation"), ("What downside remains after financing?", "Is return sufficiently compensated for modeled impairment?"), ("Downside exceeds configured margin of safety",), financial_result=model, claims=claims)


def _quant(ctx, model):
    claims = tuple(x for x in (f"IRR is {model.irr:.2%} before stochastic stress." if model is not None and model.irr is not None else None, f"Exit value is {model.exit_value:,.0f}." if model is not None and model.exit_value is not None else None) if x)
    return _assessment(ctx, "quant", "Quantitative judgment should be expressed through measurable assumptions, distributions and sensitivity rather than a single point estimate.", ("model risk", "parameter sensitivity"), ("Which variables dominate outcome variance?",), ("Distribution remains unacceptable under defined stress",), financial_result=model, claims=claims)


def _researcher(ctx, model):
    quality = ctx.evidence_quality_flags(); unknowns = tuple(f"Verify provenance for {name}." for name in ("rent_growth", "exit_cap_rate") if getattr(ctx, name, None) is not None)
    return _assessment(ctx, "researcher", "Evidence quality and provenance determine how much confidence should be placed in derived returns.", ("stale or incomplete evidence", "unsupported assumptions"), unknowns or ("Which primary sources remain unverified?",), ("Material claim cannot be independently corroborated",), "INSUFFICIENT EVIDENCE" if quality or not ctx.evidence else "WATCH", model, ("Observed, assumed and derived values must remain distinguishable.",))


def _macro(ctx, model):
    rate = ctx.interest_rate; claims = (f"Financing rate is {rate:.2%}.",) if rate is not None else ()
    if not claims and model is not None and model.annual_debt_service is not None: claims = (f"Annual debt service is {model.annual_debt_service:,.0f} under the supplied financing terms.",)
    return _assessment(ctx, "macro", "Rates, demand and the exit valuation regime can change otherwise stable property economics.", ("rate regime", "demand regime"), ("What macro regime is embedded in the exit assumption?",), ("Rates or demand move outside underwriting tolerance",), financial_result=model, claims=claims)


def _systems(ctx, model):
    claims = ()
    if model is not None and model.dscr is not None and model.break_even_occupancy is not None: claims = (f"Debt coverage is {model.dscr:.2f}x and modeled occupancy break-even is {model.break_even_occupancy:.2%}.",)
    elif model is not None and model.dscr is not None: claims = (f"Debt coverage is {model.dscr:.2f}x; occupancy break-even is UNKNOWN without explicit rent and operating-expense inputs.",)
    return _assessment(ctx, "systems", "The thesis is a dependency network involving operations, leasing, financing, capital expenditures and exit conditions.", ("dependency chains", "operational fragility"), ("Which dependency can fail first and propagate?",), ("A critical dependency lacks a credible fallback",), financial_result=model, claims=claims)


def _contrarian(ctx, model):
    claims = tuple(x for x in (f"Exit value is {model.exit_value:,.0f}, so terminal valuation is a material challenge point." if model is not None and model.exit_value is not None else None, f"Exit break-even cap rate is {model.break_even_exit_cap:.2%}." if model is not None and model.break_even_exit_cap is not None else None) if x)
    return _assessment(ctx, "contrarian", "The strongest useful case is that the apparent opportunity is mispriced because one or more central assumptions fail.", ("thesis failure", "permanent capital loss"), ("What is the strongest evidence against the deal?", "Which assumption is most fragile?"), ("A central thesis assumption is falsified",), financial_result=model, claims=claims)


def _risk(ctx, model):
    claims = tuple(x for x in (f"Base DSCR is {model.dscr:.2f}x." if model is not None and model.dscr is not None else None, f"Base net sale proceeds are {model.net_sale_proceeds:,.0f}." if model is not None and model.net_sale_proceeds is not None else None) if x)
    return _assessment(ctx, "risk", "Capital preservation requires explicit downside, leverage, liquidity, concentration, tail risk and permanent capital loss analysis before deployment.", ("leverage", "liquidity", "tail risk", "permanent capital loss"), ("What is the plausible permanent loss path?",), ("Downside cannot be contained within the configured mandate",), financial_result=model, claims=claims)


_PERSPECTIVE_BUILDERS: dict[str, Callable[[CREOpportunityContext, Any | None], PerspectiveAssessment]] = {"underwriter": _underwriter, "investor": _investor, "quant": _quant, "researcher": _researcher, "macro": _macro, "systems": _systems, "contrarian": _contrarian, "risk": _risk}


def _model_from_context(ctx: CREOpportunityContext):
    financing, exit_data, lease = ctx.financing_assumptions, ctx.exit_assumptions, ctx.leasing_assumptions
    inputs = CREFinancialInputs(purchase_price=ctx.purchase_price,noi=ctx.noi,gross_rent=ctx.gross_rent,effective_income=ctx.effective_income,occupancy=ctx.occupancy,vacancy=ctx.vacancy,operating_expenses=ctx.expenses,rent_growth=ctx.rent_growth,expense_growth=ctx.expense_growth,capital_expenditures=ctx.capital_expenditures,loan_amount=financing.get("loan_amount"),loan_to_value=financing.get("loan_to_value"),interest_rate=ctx.interest_rate if ctx.interest_rate is not None else financing.get("interest_rate"),amortization_years=financing.get("amortization_years"),interest_only=bool(financing.get("interest_only", False)),hold_period_years=int(ctx.hold_period) if ctx.hold_period is not None else None,exit_cap_rate=exit_data.get("exit_cap_rate"),selling_cost_rate=exit_data.get("selling_cost_rate"),closing_costs=exit_data.get("closing_costs"),other_income=exit_data.get("other_income"),lease_term_years=lease.get("remaining_lease_term_years"),rent_escalation=lease.get("rent_escalation"),renewal_probability=lease.get("renewal_probability"),tenant_concentration=lease.get("tenant_concentration"),tenant_credit_quality=lease.get("tenant_credit_quality"),rollover_year=lease.get("rollover_year"),downtime_years=lease.get("downtime_years"),leasing_costs=lease.get("leasing_costs"),tenant_improvements=lease.get("tenant_improvements"),evidence_ids=ctx.evidence)
    return underwrite_financial_model(inputs)


def assess_cre_opportunity(ctx: CREOpportunityContext, financial_result: Any | None = None) -> tuple[PerspectiveAssessment, ...]:
    if financial_result is None: financial_result = _model_from_context(ctx)
    return tuple(_PERSPECTIVE_BUILDERS[name](ctx, financial_result) for name in CRE_PERSPECTIVES)


def assessments_as_dicts(ctx: CREOpportunityContext, financial_result: Any | None = None) -> list[dict]:
    return [asdict(item) for item in assess_cre_opportunity(ctx, financial_result)]
