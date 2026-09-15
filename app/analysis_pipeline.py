"""Full evidence-to-decision-intelligence pipeline.

Evidence integrity precedes reasoning. Independent perspectives feed typed conflict
intelligence; risk simulation remains independent of agent conclusions. Research
context remains distinct from evidence. Meta-Intelligence evaluates the reasoning
process before synthesis. Institutional learning is advisory context only. No
execution capability exists.
"""

from dataclasses import replace
from typing import Any, Dict, Iterable

from app.conflict_intelligence import detect_conflict_intelligence
from app.decision_gate import build_decision_gate
from app.decision_readiness import build_decision_readiness
from app.evidence_orchestration import run_evidence_fed_agents
from app.institutional_core import OpportunityStatus, build_opportunity
from app.institutional_investment_case import InvestmentCaseStatus, build_institutional_investment_case
from app.kaleidoscope_view import build_kaleidoscope_view
from app.learning import build_learning_report
from app.memory import append_record, build_record, read_records
from app.meta_intelligence import evaluate as meta_intelligence_evaluate
from app.model_provider import ModelProvider
from app.observer import observe
from app.simulator import run_monte_carlo
from app.skeptic import review as skeptic_review


def detect_conflicts(agents: list[Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    """Compatibility projection of typed conflict intelligence."""
    records = detect_conflict_intelligence(agents)
    conflicts = []
    horizon_divergences = []
    for record in records:
        perspectives = record["perspectives"]
        item = {"agent_a": perspectives[0], "agent_b": perspectives[1], "type": "horizon_divergence" if record["conflict_type"] == "horizon" else "same_horizon_conflict", "conflict_type": record["conflict_type"], "conflict_record": record}
        if record["conflict_type"] == "horizon":
            horizon_divergences.append(item)
        else:
            conflicts.append(item)
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: list[Dict[str, Any]], conflict_data: Dict[str, list[Dict[str, Any]]], skeptic: Dict[str, Any], meta_intelligence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Produce transparent research synthesis; never authorize execution."""
    if any(a.get("direction") == "NO_DATA" for a in agents):
        verdict = "NO_DATA"
    elif skeptic["recommendation"] == "hold":
        verdict = "HOLD"
    elif conflict_data["conflicts"]:
        verdict = "CONDITIONAL GO"
    else:
        verdict = "INVESTIGATE"
    long_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "LONG")
    short_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "SHORT")
    total = long_score + short_score
    case_derived_questions = []
    for item in conflict_data["conflicts"] + conflict_data["horizon_divergences"]:
        case_derived_questions.extend(item.get("conflict_record", {}).get("unresolved_questions", []))
    system_questions = [
        "What evidence would invalidate the core thesis?",
        "Which assumptions are most sensitive?",
        "Does the downside case preserve an adequate margin of safety?",
    ]
    system_risks = ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"]
    return {
        "verdict": verdict,
        "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0,
        "long_evidence": round(long_score, 3),
        "short_evidence": round(short_score, 3),
        "conflict_count": len(conflict_data["conflicts"]),
        "key_risks": system_risks,
        "key_risks_provenance": "system_generated_governance_prompts",
        "case_derived_key_risks": [],
        "unresolved_questions": list(dict.fromkeys(case_derived_questions)) or system_questions,
        "case_derived_unresolved_questions": list(dict.fromkeys(case_derived_questions)),
        "system_generated_governance_questions": system_questions,
        "unresolved_questions_provenance": "case_derived_when_available_otherwise_system_generated_governance_prompts",
        "meta_intelligence": meta_intelligence or {},
    }


def run_analysis(question: str, evidence: Iterable[Dict[str, Any]], initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, now=None, max_age_seconds: float = 24 * 60 * 60, provider: ModelProvider | None = None, research_context: Dict[str, Any] | None = None, case_id: str | None = None, case_version: int = 1) -> Dict[str, Any]:
    """Run the complete research loop and assemble canonical institutional objects."""
    prior_records = read_records()
    learning_context = build_learning_report(prior_records)
    evidence_items = list(evidence)
    opportunity = build_opportunity(description=question, provenance={"origin": "analysis_request", "research_context_supplied": bool(research_context)})
    agent_stage = run_evidence_fed_agents(question, evidence_items, now=now, max_age_seconds=max_age_seconds, provider=provider, learning_context=learning_context, research_context=research_context)
    agents = agent_stage["agents"]
    validated_ids = [item.get("evidence_id") for item in evidence_items if isinstance(item, dict) and item.get("evidence_id")]
    opportunity_status = OpportunityStatus.ANALYSIS_READY if agent_stage["usable_evidence_count"] > 0 else OpportunityStatus.EVIDENCE_PENDING
    opportunity = replace(opportunity, evidence_ids=validated_ids, status=opportunity_status)
    conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(initial_value, horizon_steps, paths, seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    meta_intelligence = meta_intelligence_evaluate(agents=agents, evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}, conflicts=conflict_data["conflicts"], horizon_divergences=conflict_data["horizon_divergences"], simulation=simulation, skeptic=skeptic, learning_context=learning_context)
    synthesis = synthesize(agents, conflict_data, skeptic, meta_intelligence)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False, "investment_authority": False}
    evidence_state = {"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}
    perspective_provenance = [
        {
            "agent_id": agent.get("agent_id"),
            "evidence_basis": agent.get("evidence_basis", []),
            "reasoning_method": agent.get("strategy", "unknown"),
            "model_version": agent.get("model_version"),
            "independence": "shared_pipeline_inputs",
            "independence_limitation": "Separate perspective identity does not by itself establish model independence.",
        }
        for agent in agents
        if isinstance(agent, dict)
    ]
    institutional_case = build_institutional_investment_case(
        question,
        opportunity=opportunity.to_dict(),
        opportunity_id=opportunity.opportunity_id,
        evidence=evidence_items,
        evidence_summary=evidence_state,
        assumptions=[a for agent in agents for a in agent.get("assumptions", [])],
        scenarios=simulation.get("scenarios"),
        risk=simulation,
        perspectives=agents,
        perspective_provenance=perspective_provenance,
        conflicts=conflict_data,
        contrarian_review=skeptic,
        synthesis=synthesis,
        governance=governance,
        domain="shared",
        case_id=case_id,
        case_version=case_version,
    )
    decision_readiness = build_decision_readiness(institutional_case, evidence=evidence_state, simulation=simulation, skeptic=skeptic, synthesis=synthesis, governance=governance)
    institutional_case.decision_readiness = decision_readiness
    if decision_readiness["status"] == "READY_FOR_HUMAN_AUTHORITY":
        institutional_case.status = InvestmentCaseStatus.READY_FOR_HUMAN_AUTHORITY
    decision_gate = build_decision_gate(
        evidence_state, conflict_data, simulation, skeptic, synthesis, governance,
        contrarian_status="present" if any(a.get("agent_id") == "contrarian" for a in agents) else "not_available",
        decision_readiness=decision_readiness,
    )
    observer = observe(question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(question, agents, conflict_data, simulation, skeptic, synthesis, governance, seed, decision_gate=decision_gate, meta_intelligence=meta_intelligence)
    record["opportunity"] = opportunity.to_dict()
    record["investment_case_id"] = institutional_case.case_id
    record["institutional_investment_case"] = institutional_case.to_dict()
    record["institutional_learning_context"] = {"resolved_prediction_count": learning_context.get("resolved_prediction_count", 0), "lessons": learning_context.get("lessons", []), "agent_metrics_ranked": learning_context.get("agent_metrics_ranked", []), "horizon_metrics": learning_context.get("horizon_metrics", {}), "informational_only": True}
    record["research_context"] = research_context or {}
    append_record(record)
    kaleidoscope = build_kaleidoscope_view(agents=agents, evidence=evidence_state, conflicts=conflict_data["conflicts"], horizon_divergences=conflict_data["horizon_divergences"], simulation=simulation, skeptic=skeptic, meta_intelligence=meta_intelligence, synthesis=synthesis, observer=observer, governance=governance)
    return {"system": "AletheiaTelos", "question": question, "opportunity": opportunity.to_dict(), "institutional_investment_case": institutional_case.to_dict(), "institutional_learning": learning_context, "research_context": research_context or {}, "evidence": evidence_state, "agents": agents, "active_perspectives": agent_stage["active_perspectives"], "reasoning_perspectives": agent_stage["reasoning_perspectives"], "registered_agent_count": agent_stage["registered_agent_count"], "conflicts": conflict_data["conflicts"], "horizon_divergences": conflict_data["horizon_divergences"], "conflict_intelligence": conflict_data["conflicts"] + conflict_data["horizon_divergences"], "simulation": simulation, "skeptic": skeptic, "meta_intelligence": meta_intelligence, "synthesis": synthesis, "decision_readiness": decision_readiness, "decision_gate": decision_gate, "observer": observer, "governance": governance, "kaleidoscope": kaleidoscope, "audit": {"pipeline": "opportunity->evidence->independent_perspectives->conflict_intelligence->independent_risk->skeptic->meta_intelligence->synthesis->investment_case->decision_readiness->decision_gate->human_authority->decision_record->observer->memory", "simulation_independent_of_agents": True, "simulation_seed": seed, "memory_recorded": True, "research_only": True, "human_decision_required": True, "decision_gate_state": decision_gate["state"], "ready_for_human_authority": decision_gate["ready_for_human_authority"], "investment_case_id": institutional_case.case_id, "investment_case_version": institutional_case.case_version, "opportunity_id": opportunity.opportunity_id, "provider": agent_stage["provider"], "learning_context_supplied": agent_stage["learning_context_supplied"], "research_context_supplied": agent_stage["research_context_supplied"], "perspectives_share_conclusions": agent_stage["perspectives_share_conclusions"], "meta_intelligence_directional_vote": False, "meta_intelligence_execution_capability": False}}
