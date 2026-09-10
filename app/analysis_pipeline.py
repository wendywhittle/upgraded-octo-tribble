"""Full evidence-to-decision-intelligence pipeline.

Evidence integrity precedes reasoning. CRE perspectives consume one shared financial
model; conflict preserves disagreement; simulation remains independent of conclusions.
No execution capability exists in this module.
"""
from typing import Any, Dict, Iterable

from app.conflict_intelligence import detect_conflict_intelligence, detect_cre_conflicts
from app.cre_adversarial import review_cre_simulation
from app.cre_context import CREOpportunityContext
from app.cre_decision import CREDecisionCriteria, build_decision_record, evaluate_financial_decision
from app.cre_perspectives import assess_cre_opportunity
from app.cre_underwriting import Assumption, CREFinancialInputs, Property, UnderwritingInputs, underwrite, underwrite_financial_model
from app.evidence_orchestration import run_evidence_fed_agents
from app.kaleidoscope_view import build_kaleidoscope_view
from app.learning import build_learning_report
from app.memory import append_record, build_record, read_records
from app.meta_intelligence import evaluate as meta_intelligence_evaluate
from app.model_provider import ModelProvider
from app.observer import observe
from app.simulator import run_monte_carlo, run_cre_monte_carlo
from app.skeptic import review as skeptic_review


def detect_conflicts(agents: list[Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    records = detect_conflict_intelligence(agents)
    conflicts, horizon_divergences = [], []
    for record in records:
        perspectives = record["perspectives"]
        item = {"agent_a": perspectives[0], "agent_b": perspectives[1], "type": "horizon_divergence" if record["conflict_type"] == "horizon" else "same_horizon_conflict", "conflict_type": record["conflict_type"], "conflict_record": record}
        (horizon_divergences if record["conflict_type"] == "horizon" else conflicts).append(item)
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: list[Dict[str, Any]], conflict_data: Dict[str, list[Dict[str, Any]]], skeptic: Dict[str, Any], meta_intelligence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if any(a.get("direction") == "NO_DATA" for a in agents): verdict = "NO_DATA"
    elif skeptic["recommendation"] == "hold": verdict = "HOLD"
    elif conflict_data["conflicts"]: verdict = "CONDITIONAL GO"
    else: verdict = "INVESTIGATE"
    long_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "LONG")
    short_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "SHORT")
    total = long_score + short_score
    unresolved = []
    for item in conflict_data["conflicts"] + conflict_data["horizon_divergences"]:
        unresolved.extend(item.get("conflict_record", {}).get("unresolved_questions", []))
    return {"verdict": verdict, "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0, "long_evidence": round(long_score, 3), "short_evidence": round(short_score, 3), "conflict_count": len(conflict_data["conflicts"]), "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"], "unresolved_questions": list(dict.fromkeys(unresolved)) or ["What evidence would invalidate the core thesis?", "Which assumptions are most sensitive?", "Does the downside case preserve an adequate margin of safety?"], "meta_intelligence": meta_intelligence or {}}


def _underwriting_from_context(ctx: CREOpportunityContext):
    property_data = Property(ctx.property_id, ctx.asset_type, ctx.location, occupancy=ctx.occupancy, tenant_concentration=ctx.leasing_assumptions.get("tenant_concentration"), lease_type=ctx.leasing_assumptions.get("lease_type"), remaining_lease_term_years=ctx.leasing_assumptions.get("remaining_lease_term_years"))
    assumptions = tuple(Assumption(name=name, value=name, unit="context", evidence_id=None) for name in ctx.assumptions)
    return underwrite(UnderwritingInputs(opportunity_id=ctx.opportunity_id, property=property_data, purchase_price=ctx.purchase_price, annual_noi=ctx.noi, assumptions=assumptions, evidence_ids=ctx.evidence, contradictory_evidence=ctx.contradictory_evidence, uncertainty_notes=ctx.uncertainty))


def _financial_inputs_from_context(ctx: CREOpportunityContext) -> CREFinancialInputs:
    financing, exit, lease = ctx.financing_assumptions, ctx.exit_assumptions, ctx.leasing_assumptions
    return CREFinancialInputs(
        purchase_price=ctx.purchase_price, noi=ctx.noi, gross_rent=ctx.gross_rent, effective_income=ctx.effective_income,
        occupancy=ctx.occupancy, vacancy=ctx.vacancy, operating_expenses=ctx.expenses, rent_growth=ctx.rent_growth,
        expense_growth=ctx.expense_growth, capital_expenditures=ctx.capital_expenditures, loan_amount=financing.get("loan_amount"),
        loan_to_value=financing.get("loan_to_value"), interest_rate=ctx.interest_rate if ctx.interest_rate is not None else financing.get("interest_rate"),
        amortization_years=financing.get("amortization_years"), interest_only=bool(financing.get("interest_only", False)),
        hold_period_years=int(ctx.hold_period) if ctx.hold_period is not None else None, exit_cap_rate=exit.get("exit_cap_rate"),
        selling_cost_rate=exit.get("selling_cost_rate"), closing_costs=exit.get("closing_costs"), other_income=exit.get("other_income"),
        lease_term_years=lease.get("remaining_lease_term_years"), rent_escalation=lease.get("rent_escalation"), renewal_probability=lease.get("renewal_probability"),
        tenant_concentration=lease.get("tenant_concentration"), tenant_credit_quality=lease.get("tenant_credit_quality"), rollover_year=lease.get("rollover_year"),
        downtime_years=lease.get("downtime_years"), leasing_costs=lease.get("leasing_costs"), tenant_improvements=lease.get("tenant_improvements"), evidence_ids=ctx.evidence,
    )


def run_analysis(question: str, evidence: Iterable[Dict[str, Any]], initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, now=None, max_age_seconds: float = 24 * 60 * 60, provider: ModelProvider | None = None, cre_assessments: Iterable[Dict[str, Any]] = (), cre_context: CREOpportunityContext | None = None, cre_criteria: CREDecisionCriteria | None = None) -> Dict[str, Any]:
    prior_records = read_records(); learning_context = build_learning_report(prior_records)
    agent_stage = run_evidence_fed_agents(question, evidence, now=now, max_age_seconds=max_age_seconds, provider=provider, learning_context=learning_context)
    agents = agent_stage["agents"]; conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(initial_value, horizon_steps, paths, seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    meta_intelligence = meta_intelligence_evaluate(agents=agents, evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}, conflicts=conflict_data["conflicts"], horizon_divergences=conflict_data["horizon_divergences"], simulation=simulation, skeptic=skeptic, learning_context=learning_context)
    synthesis = synthesize(agents, conflict_data, skeptic, meta_intelligence)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False}
    observer = observe(question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(question, agents, conflict_data, simulation, skeptic, synthesis, governance, seed); record["meta_intelligence"] = meta_intelligence
    record["institutional_learning_context"] = {"resolved_prediction_count": learning_context.get("resolved_prediction_count", 0), "lessons": learning_context.get("lessons", []), "agent_metrics_ranked": learning_context.get("agent_metrics_ranked", []), "horizon_metrics": learning_context.get("horizon_metrics", {}), "informational_only": True}; append_record(record)

    cre_result: dict[str, Any] = {}; cre_for_view = tuple(cre_assessments)
    if cre_context is not None:
        underwriting = _underwriting_from_context(cre_context)
        financial_inputs = _financial_inputs_from_context(cre_context)
        financial_model = underwrite_financial_model(financial_inputs)
        financing, exit = cre_context.financing_assumptions, cre_context.exit_assumptions
        cre_simulation = run_cre_monte_carlo(
            purchase_price=cre_context.purchase_price, noi=cre_context.noi, hold_period=int(cre_context.hold_period or 5), paths=paths, seed=seed,
            occupancy=cre_context.occupancy, rent_growth=cre_context.rent_growth, expense_growth=cre_context.expense_growth,
            interest_rate=financial_inputs.interest_rate, loan_to_value=financing.get("loan_to_value"), capital_expenditures=cre_context.capital_expenditures,
            assumptions=list(cre_context.assumption_labels()), gross_rent=cre_context.gross_rent, operating_expenses=cre_context.expenses,
            vacancy=cre_context.vacancy, amortization_years=financial_inputs.amortization_years, exit_cap_rate=exit.get("exit_cap_rate"),
            selling_cost_rate=financial_inputs.selling_cost_rate, interest_only=financial_inputs.interest_only, closing_costs=financial_inputs.closing_costs,
            other_income=financial_inputs.other_income,
        )
        assessments = assess_cre_opportunity(cre_context, financial_model)
        cre_conflicts = detect_cre_conflicts(assessments)
        cre_adversarial = review_cre_simulation(cre_simulation, cre_context.assumption_labels(), cre_context.evidence)
        if cre_criteria is not None:
            decision = evaluate_financial_decision(financial_model, cre_criteria, supplied_ltv=financing.get("loan_to_value"))
            decision = type(decision)(state=decision.state, rationale=decision.rationale, unresolved_questions=tuple(cre_adversarial.unresolved_questions) + tuple(cre_context.uncertainty), evidence_ids=decision.evidence_ids)
        else:
            decision = build_decision_record(underwriting, unresolved_questions=tuple(cre_adversarial.unresolved_questions) + tuple(cre_context.uncertainty))
        cre_for_view = assessments
        cre_result = {"context": cre_context, "underwriting": underwriting, "financial_model": financial_model, "perspectives": assessments, "conflicts": cre_conflicts, "simulation": cre_simulation, "adversarial_review": cre_adversarial, "decision": decision, "decision_boundary": "human authority required"}

    kaleidoscope = build_kaleidoscope_view(agents=agents, evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}, conflicts=conflict_data["conflicts"], horizon_divergences=conflict_data["horizon_divergences"], simulation=simulation, skeptic=skeptic, meta_intelligence=meta_intelligence, synthesis=synthesis, observer=observer, governance=governance, cre_assessments=cre_for_view)
    return {"system": "AletheiaTelos", "question": question, "institutional_learning": learning_context, "evidence": {"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}, "agents": agents, "active_perspectives": agent_stage["active_perspectives"], "reasoning_perspectives": agent_stage["reasoning_perspectives"], "registered_agent_count": agent_stage["registered_agent_count"], "conflicts": conflict_data["conflicts"], "horizon_divergences": conflict_data["horizon_divergences"], "conflict_intelligence": conflict_data["conflicts"] + conflict_data["horizon_divergences"], "simulation": simulation, "skeptic": skeptic, "meta_intelligence": meta_intelligence, "synthesis": synthesis, "observer": observer, "governance": governance, "kaleidoscope": kaleidoscope, "cre": cre_result, "audit": {"pipeline": "prior_learning->evidence->cre_context->underwriting->financial_model->cre_perspectives->cre_conflict->independent_cre_simulation->cre_adversarial_review->decision->human_authority", "simulation_independent_of_agents": True, "simulation_seed": seed, "memory_recorded": True, "research_only": True, "human_decision_required": True, "provider": agent_stage["provider"], "learning_context_supplied": agent_stage["learning_context_supplied"], "perspectives_share_conclusions": agent_stage["perspectives_share_conclusions"], "meta_intelligence_directional_vote": False, "meta_intelligence_execution_capability": False, "cre_assessments_are_observational": True, "cre_simulation_independent_of_perspectives": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False}}
