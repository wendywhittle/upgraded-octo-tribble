"""Full evidence-to-decision-intelligence pipeline.

Evidence integrity precedes reasoning. Independent perspectives feed typed conflict
intelligence; risk simulation remains independent of agent conclusions. Meta-Intelligence
evaluates the reasoning process before synthesis. Institutional learning is advisory
context only. No execution capability exists in this module.
"""

from typing import Any, Dict, Iterable

from app.conflict_intelligence import detect_conflict_intelligence
from app.evidence_orchestration import run_evidence_fed_agents
from app.investment_case import build_structured_investment_case
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
        item = {
            "agent_a": perspectives[0],
            "agent_b": perspectives[1],
            "type": "horizon_divergence" if record["conflict_type"] == "horizon" else "same_horizon_conflict",
            "conflict_type": record["conflict_type"],
            "conflict_record": record,
        }
        if record["conflict_type"] == "horizon":
            horizon_divergences.append(item)
        else:
            conflicts.append(item)
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: list[Dict[str, Any]], conflict_data: Dict[str, list[Dict[str, Any]]], skeptic: Dict[str, Any], meta_intelligence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Produce a transparent research synthesis; never authorize execution."""
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
    unresolved = []
    for item in conflict_data["conflicts"] + conflict_data["horizon_divergences"]:
        unresolved.extend(item.get("conflict_record", {}).get("unresolved_questions", []))
    return {
        "verdict": verdict,
        "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0,
        "long_evidence": round(long_score, 3),
        "short_evidence": round(short_score, 3),
        "conflict_count": len(conflict_data["conflicts"]),
        "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"],
        "unresolved_questions": list(dict.fromkeys(unresolved)) or [
            "What evidence would invalidate the core thesis?",
            "Which assumptions are most sensitive?",
            "Does the downside case preserve an adequate margin of safety?",
        ],
        "meta_intelligence": meta_intelligence or {},
    }


def run_analysis(question: str, evidence: Iterable[Dict[str, Any]], initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, now=None, max_age_seconds: float = 24 * 60 * 60, provider: ModelProvider | None = None) -> Dict[str, Any]:
    """Run the complete research loop and persist an auditable learning record."""
    prior_records = read_records()
    learning_context = build_learning_report(prior_records)
    agent_stage = run_evidence_fed_agents(
        question,
        evidence,
        now=now,
        max_age_seconds=max_age_seconds,
        provider=provider,
        learning_context=learning_context,
    )
    agents = agent_stage["agents"]
    conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(initial_value, horizon_steps, paths, seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    meta_intelligence = meta_intelligence_evaluate(
        agents=agents,
        evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]},
        conflicts=conflict_data["conflicts"],
        horizon_divergences=conflict_data["horizon_divergences"],
        simulation=simulation,
        skeptic=skeptic,
        learning_context=learning_context,
    )
    synthesis = synthesize(agents, conflict_data, skeptic, meta_intelligence)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False}
    observer = observe(question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(question, agents, conflict_data, simulation, skeptic, synthesis, governance, seed)
    record["meta_intelligence"] = meta_intelligence
    record["institutional_learning_context"] = {
        "resolved_prediction_count": learning_context.get("resolved_prediction_count", 0),
        "lessons": learning_context.get("lessons", []),
        "agent_metrics_ranked": learning_context.get("agent_metrics_ranked", []),
        "horizon_metrics": learning_context.get("horizon_metrics", {}),
        "informational_only": True,
    }
    append_record(record)
    kaleidoscope = build_kaleidoscope_view(
        agents=agents,
        evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]},
        conflicts=conflict_data["conflicts"],
        horizon_divergences=conflict_data["horizon_divergences"],
        simulation=simulation,
        skeptic=skeptic,
        meta_intelligence=meta_intelligence,
        synthesis=synthesis,
        observer=observer,
        governance=governance,
    )
    evidence_for_case = {
        "count": agent_stage["evidence_count"],
        "usable_count": agent_stage["usable_evidence_count"],
        "validation": agent_stage["validation"],
        "items": agent_stage.get("usable_evidence", []),
    }
    investment_case = build_structured_investment_case(
        question=question,
        evidence=evidence_for_case,
        agents=agents,
        simulation=simulation,
        skeptic=skeptic,
        synthesis=synthesis,
        meta_intelligence=meta_intelligence,
        created_at=now,
    )
    return {
        "system": "AletheiaTelos",
        "question": question,
        "institutional_learning": learning_context,
        "evidence": evidence_for_case,
        "agents": agents,
        "active_perspectives": agent_stage["active_perspectives"],
        "reasoning_perspectives": agent_stage["reasoning_perspectives"],
        "registered_agent_count": agent_stage["registered_agent_count"],
        "conflicts": conflict_data["conflicts"],
        "horizon_divergences": conflict_data["horizon_divergences"],
        "conflict_intelligence": conflict_data["conflicts"] + conflict_data["horizon_divergences"],
        "simulation": simulation,
        "skeptic": skeptic,
        "meta_intelligence": meta_intelligence,
        "synthesis": synthesis,
        "observer": observer,
        "governance": governance,
        "kaleidoscope": kaleidoscope,
        "structured_investment_case": investment_case.model_dump(mode="json"),
        "audit": {
            "pipeline": "prior_learning->evidence->independent_perspectives->conflict_intelligence->independent_risk->skeptic->meta_intelligence->synthesis->structured_investment_case->human_decision_gate",
            "simulation_independent_of_agents": True,
            "simulation_seed": seed,
            "memory_recorded": True,
            "research_only": True,
            "human_decision_required": True,
            "provider": agent_stage["provider"],
            "learning_context_supplied": agent_stage["learning_context_supplied"],
            "perspectives_share_conclusions": agent_stage["perspectives_share_conclusions"],
            "meta_intelligence_directional_vote": False,
            "meta_intelligence_execution_capability": False,
            "investment_case_is_authorization": False,
            "human_decision_gate_pending": True,
        },
    }
