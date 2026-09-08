"""Full evidence-to-decision-intelligence pipeline.

The pipeline is deliberately ordered so evidence integrity precedes reasoning, while
risk simulation remains independent of agent conclusions. No execution capability exists.
"""

from typing import Any, Dict, Iterable

from app.evidence_orchestration import run_evidence_fed_agents
from app.memory import append_record, build_record
from app.observer import observe
from app.simulator import run_monte_carlo
from app.skeptic import review as skeptic_review


def _detect_conflicts(agents: list[Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    conflicts, horizon_divergences = [], []
    for i, first in enumerate(agents):
        for second in agents[i + 1:]:
            if first.get("direction") in {"NEUTRAL", "NO_DATA"} or second.get("direction") in {"NEUTRAL", "NO_DATA"} or first.get("direction") == second.get("direction"):
                continue
            if first.get("horizon") == second.get("horizon"):
                conflicts.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first["direction"], "direction_b": second["direction"], "horizon": first["horizon"], "type": "same_horizon_conflict"})
            else:
                horizon_divergences.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first["direction"], "direction_b": second["direction"], "horizon_a": first["horizon"], "horizon_b": second["horizon"], "type": "horizon_divergence"})
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def _synthesize(agents: list[Dict[str, Any]], conflicts: Dict[str, list[Dict[str, Any]]], skeptic: Dict[str, Any]) -> Dict[str, Any]:
    if any(a.get("direction") == "NO_DATA" for a in agents):
        verdict = "NO_DATA"
    elif skeptic["recommendation"] == "hold":
        verdict = "HOLD"
    elif conflicts["conflicts"]:
        verdict = "CONDITIONAL GO"
    else:
        verdict = "INVESTIGATE"
    long_score = sum(a["confidence"] for a in agents if a.get("direction") == "LONG")
    short_score = sum(a["confidence"] for a in agents if a.get("direction") == "SHORT")
    total = long_score + short_score
    return {
        "verdict": verdict,
        "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0,
        "long_evidence": round(long_score, 3),
        "short_evidence": round(short_score, 3),
        "conflict_count": len(conflicts["conflicts"]),
        "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"],
        "unresolved_questions": ["What evidence would invalidate the core thesis?", "Which assumptions are most sensitive?", "Does the downside case preserve an adequate margin of safety?"],
    }


def run_analysis(
    question: str,
    evidence: Iterable[Dict[str, Any]],
    initial_value: float = 100.0,
    horizon_steps: int = 60,
    paths: int = 5000,
    seed: int = 42,
    now=None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Run evidence, perspectives, conflict, risk, skepticism, synthesis and learning."""
    agent_stage = run_evidence_fed_agents(question, evidence, now=now, max_age_seconds=max_age_seconds)
    agents = agent_stage["agents"]
    conflicts = _detect_conflicts(agents)

    simulation = run_monte_carlo(
        initial_value,
        horizon_steps,
        paths,
        seed,
        assumptions=[a for agent in agents for a in agent.get("assumptions", [])],
    )
    skeptic = skeptic_review(agents, simulation)
    synthesis = _synthesize(agents, conflicts, skeptic)
    governance = {
        "human_decision_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }
    observer = observe(question, agents, conflicts, simulation, skeptic, synthesis)
    record = build_record(question, agents, conflicts, simulation, skeptic, synthesis, governance, seed)
    append_record(record)

    return {
        "question": question,
        "evidence": {
            "count": agent_stage["evidence_count"],
            "usable_count": agent_stage["usable_evidence_count"],
            "validation": agent_stage["validation"],
        },
        "agents": agents,
        "conflicts": conflicts["conflicts"],
        "horizon_divergences": conflicts["horizon_divergences"],
        "simulation": simulation,
        "skeptic": skeptic,
        "synthesis": synthesis,
        "observer": observer,
        "governance": governance,
        "audit": {
            "pipeline": "evidence->agents->conflict->independent_risk->skeptic->synthesis->governance->observer->memory",
            "simulation_independent_of_agents": True,
            "simulation_seed": seed,
            "memory_recorded": True,
            "research_only": True,
            "human_decision_required": True,
        },
    }
