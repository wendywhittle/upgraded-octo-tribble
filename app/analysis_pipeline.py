"""Full evidence-to-decision-intelligence pipeline.

Evidence integrity precedes reasoning. Risk simulation is independent of agent
conclusions. No execution capability exists in this module.
"""

from typing import Any, Dict, Iterable

from app.evidence_orchestration import run_evidence_fed_agents
from app.kaleidoscope_view import build_kaleidoscope_view
from app.memory import append_record, build_record
from app.model_provider import ModelProvider
from app.observer import observe
from app.simulator import run_monte_carlo
from app.skeptic import review as skeptic_review


def detect_conflicts(agents: list[Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    """Record disagreement explicitly instead of averaging it away."""
    conflicts: list[Dict[str, Any]] = []
    horizon_divergences: list[Dict[str, Any]] = []
    for i, first in enumerate(agents):
        for second in agents[i + 1:]:
            first_direction = first.get("direction")
            second_direction = second.get("direction")
            if first_direction in {"NEUTRAL", "NO_DATA"} or second_direction in {"NEUTRAL", "NO_DATA"}:
                continue
            if first_direction == second_direction:
                continue
            if first.get("horizon") == second.get("horizon"):
                conflicts.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first_direction, "direction_b": second_direction, "horizon": first.get("horizon"), "type": "same_horizon_conflict"})
            else:
                horizon_divergences.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first_direction, "direction_b": second_direction, "horizon_a": first.get("horizon"), "horizon_b": second.get("horizon"), "type": "horizon_divergence"})
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: list[Dict[str, Any]], conflict_data: Dict[str, list[Dict[str, Any]]], skeptic: Dict[str, Any]) -> Dict[str, Any]:
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
    return {"verdict": verdict, "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0, "long_evidence": round(long_score, 3), "short_evidence": round(short_score, 3), "conflict_count": len(conflict_data["conflicts"]), "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"], "unresolved_questions": ["What evidence would invalidate the core thesis?", "Which assumptions are most sensitive?", "Does the downside case preserve an adequate margin of safety?"]}


def run_analysis(question: str, evidence: Iterable[Dict[str, Any]], initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, now=None, max_age_seconds: float = 24 * 60 * 60, provider: ModelProvider | None = None) -> Dict[str, Any]:
    """Run the complete research loop and persist an auditable learning record."""
    agent_stage = run_evidence_fed_agents(question, evidence, now=now, max_age_seconds=max_age_seconds, provider=provider)
    agents = agent_stage["agents"]
    conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(initial_value, horizon_steps, paths, seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    synthesis = synthesize(agents, conflict_data, skeptic)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False, "portfolio_mutation": False}
    observer = observe(question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(question, agents, conflict_data, simulation, skeptic, synthesis, governance, seed)
    append_record(record)
    kaleidoscope = build_kaleidoscope_view(
        agents=agents,
        evidence={"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]},
        conflicts=conflict_data["conflicts"],
        horizon_divergences=conflict_data["horizon_divergences"],
        simulation=simulation,
        skeptic=skeptic,
        synthesis=synthesis,
        observer=observer,
        governance=governance,
    )
    return {"system": "AletheiaTelos", "question": question, "evidence": {"count": agent_stage["evidence_count"], "usable_count": agent_stage["usable_evidence_count"], "validation": agent_stage["validation"]}, "agents": agents, "conflicts": conflict_data["conflicts"], "horizon_divergences": conflict_data["horizon_divergences"], "simulation": simulation, "skeptic": skeptic, "synthesis": synthesis, "observer": observer, "governance": governance, "kaleidoscope": kaleidoscope, "audit": {"pipeline": "evidence->agents->conflict->independent_risk->skeptic->synthesis->governance->observer->memory->kaleidoscope", "simulation_independent_of_agents": True, "simulation_seed": seed, "memory_recorded": True, "research_only": True, "human_decision_required": True, "provider": agent_stage["provider"]}}
