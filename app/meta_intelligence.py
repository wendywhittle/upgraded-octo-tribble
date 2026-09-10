"""Process-level evaluation of reasoning-system health.

Meta-Intelligence is deliberately not a directional agent. It evaluates the
behavior and quality of the reasoning process across perspectives after conflict,
risk simulation, and Skeptic review, before synthesis.
"""

from typing import Any, Dict, Iterable


_REASONING_AGENT_IDS = {
    "researcher",
    "quant",
    "investor",
    "scientist",
    "systems",
    "skeptic",
    "contrarian",
    "governance",
}


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def evaluate(
    agents: Iterable[Dict[str, Any]],
    evidence: Dict[str, Any] | None = None,
    conflicts: Iterable[Dict[str, Any]] = (),
    horizon_divergences: Iterable[Dict[str, Any]] = (),
    simulation: Dict[str, Any] | None = None,
    skeptic: Dict[str, Any] | None = None,
    learning_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Evaluate the reasoning process without voting on its directional conclusion."""
    agent_list = [dict(agent) for agent in agents if agent.get("agent_id") in _REASONING_AGENT_IDS]
    evidence = evidence or {}
    simulation = simulation or {}
    skeptic = skeptic or {}
    conflicts = [dict(item) for item in conflicts]
    horizon_divergences = [dict(item) for item in horizon_divergences]

    observations: list[str] = []
    false_consensus_signals: list[str] = []
    correlated_reasoning_signals: list[str] = []
    evidence_concerns: list[str] = []
    assumption_concentration: list[str] = []
    uncertainty_concerns: list[str] = []
    regime_concerns: list[str] = []
    blind_spots: list[str] = []

    directional = [a for a in agent_list if a.get("direction") in {"LONG", "SHORT"}]
    grouped_directions: Dict[str, list[Dict[str, Any]]] = {"LONG": [], "SHORT": []}
    for agent in directional:
        grouped_directions[agent["direction"]].append(agent)

    for direction, group in grouped_directions.items():
        if len(group) < 2:
            continue
        evidence_sets = [
            {str(item.get("evidence_id")) for item in agent.get("evidence", []) if item.get("evidence_id")}
            for agent in group
        ]
        shared = set.intersection(*evidence_sets) if evidence_sets else set()
        assumption_sets = [set(str(item) for item in agent.get("assumptions", [])) for agent in group]
        shared_assumptions = set.intersection(*assumption_sets) if assumption_sets else set()
        if shared or shared_assumptions:
            detail = f"{direction} agreement has shared reasoning inputs"
            if shared:
                detail += f" (evidence: {', '.join(sorted(shared))})"
            if shared_assumptions:
                detail += f" (assumptions: {', '.join(sorted(shared_assumptions))})"
            false_consensus_signals.append(detail)
            correlated_reasoning_signals.append(detail)

    if directional and len({a.get("direction") for a in directional}) == 1 and len(directional) >= 3:
        false_consensus_signals.append("Multiple directional perspectives agree; apparent consensus should not be counted as independent confirmation without distinct evidence or assumptions.")

    if not agent_list:
        evidence_concerns.append("No reasoning perspectives were available for process evaluation.")
    elif any(not a.get("evidence") for a in agent_list if a.get("direction") != "NO_DATA"):
        evidence_concerns.append("At least one reasoning perspective lacks explicit evidence provenance.")

    if evidence.get("count", 0) and not evidence.get("usable_count", 0):
        evidence_concerns.append("Supplied evidence was not decision-usable after validation.")

    assumption_counts: Dict[str, int] = {}
    for agent in agent_list:
        for assumption in agent.get("assumptions", []):
            key = str(assumption).strip()
            if key:
                assumption_counts[key] = assumption_counts.get(key, 0) + 1
    for assumption, count in sorted(assumption_counts.items(), key=lambda item: (-item[1], item[0])):
        if count >= 2:
            assumption_concentration.append(f"Assumption appears in {count} perspectives: {assumption}")

    unresolved_records = [
        item for item in conflicts + horizon_divergences
        if item.get("conflict_record", {}).get("status", "unresolved") != "resolved"
    ]
    unresolved_questions = _unique(
        question
        for item in unresolved_records
        for question in item.get("conflict_record", {}).get("unresolved_questions", [])
    )
    if unresolved_records:
        observations.append(f"{len(unresolved_records)} unresolved conflict or horizon-divergence record(s) remain visible before synthesis.")

    if any(a.get("confidence", 0.0) >= 0.75 for a in directional) and evidence_concerns:
        uncertainty_concerns.append("At least one directional perspective has high confidence while evidence-quality concerns remain.")
    if unresolved_records:
        uncertainty_concerns.append("Material disagreement remains unresolved; confidence should not be interpreted as consensus certainty.")
    if simulation and not simulation.get("independent_of_agents", False):
        uncertainty_concerns.append("Simulation independence is not established.")

    for agent in agent_list:
        if not agent.get("invalidation_conditions") and agent.get("direction") in {"LONG", "SHORT"}:
            regime_concerns.append(f"{agent.get('agent_id')} has no explicit invalidation conditions for its directional conclusion.")
        if agent.get("regime_assumption"):
            regime_concerns.append(f"{agent.get('agent_id')} depends on a regime assumption: {agent['regime_assumption']}")

    directional_ids = {a.get("agent_id") for a in directional}
    if directional_ids and all(not a.get("contradictory_evidence") for a in directional):
        blind_spots.append("Directional perspectives report no explicit contradictory evidence; downside challenge may be incomplete.")
    if not conflicts and not horizon_divergences and len(directional) >= 2:
        blind_spots.append("No structured conflict is present; verify that agreement is not being mistaken for independence.")
    if not skeptic.get("challenges") and agent_list:
        blind_spots.append("Skeptic reported no challenges; this should be treated as a process observation, not proof of robustness.")

    risk_count = sum(bool(group) for group in (
        false_consensus_signals,
        correlated_reasoning_signals,
        evidence_concerns,
        assumption_concentration,
        unresolved_questions,
        uncertainty_concerns,
        regime_concerns,
        blind_spots,
    ))
    if not agent_list:
        reasoning_health = "INSUFFICIENT"
    elif len(evidence_concerns) and not directional:
        reasoning_health = "INSUFFICIENT"
    elif risk_count >= 5:
        reasoning_health = "DEGRADED"
    elif risk_count >= 2:
        reasoning_health = "CAUTION"
    else:
        reasoning_health = "HEALTHY"

    if evidence_concerns or not agent_list:
        next_step = "GATHER_MORE_EVIDENCE"
    elif unresolved_records:
        next_step = "INVESTIGATE_CONFLICT"
    elif assumption_concentration:
        next_step = "TEST_ASSUMPTIONS"
    elif uncertainty_concerns or regime_concerns:
        next_step = "REVIEW_SCENARIOS"
    else:
        next_step = "PROCEED_TO_SYNTHESIS"

    observations.extend(false_consensus_signals)
    observations.extend(evidence_concerns)
    observations.extend(assumption_concentration)
    observations.extend(uncertainty_concerns)
    observations.extend(regime_concerns)
    observations.extend(blind_spots)

    return {
        "status": "evaluated",
        "reasoning_health": reasoning_health,
        "false_consensus_risk": "HIGH" if len(false_consensus_signals) >= 2 else ("MEDIUM" if false_consensus_signals else "LOW"),
        "correlated_reasoning_risk": "HIGH" if len(correlated_reasoning_signals) >= 2 else ("MEDIUM" if correlated_reasoning_signals else "LOW"),
        "evidence_quality_concern": evidence_concerns,
        "assumption_concentration": assumption_concentration,
        "unresolved_conflicts": unresolved_questions,
        "uncertainty_concern": uncertainty_concerns,
        "regime_or_invalidation_concern": regime_concerns,
        "process_blind_spots": blind_spots,
        "recommended_next_step": next_step,
        "observations": observations,
        "human_review_required": True,
        "directional_vote": None,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "learning_context_used": bool(learning_context),
    }
