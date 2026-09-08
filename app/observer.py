"""Independent Observer: records what the system believed and what remains unknown."""

from typing import Any, Dict, List


def observe(question: str, agents: List[Dict[str, Any]], conflicts: Dict[str, Any],
            simulation: Dict[str, Any], skeptic: Dict[str, Any],
            synthesis: Dict[str, Any]) -> Dict[str, Any]:
    dissent = [
        {"agent_id": a.get("agent_id"), "direction": a.get("direction"),
         "confidence": a.get("confidence")} for a in agents
        if a.get("direction") in {"LONG", "SHORT"}
    ]
    return {
        "status": "observed",
        "question": question,
        "agent_count": len(agents),
        "same_horizon_conflicts": len(conflicts.get("conflicts", [])),
        "horizon_divergences": len(conflicts.get("horizon_divergences", [])),
        "dissenting_perspectives": dissent,
        "simulation_independent": simulation.get("independent_of_agents", False),
        "skeptic_recommendation": skeptic.get("recommendation"),
        "synthesis_verdict": synthesis.get("verdict"),
        "outcome_status": "pending",
        "learning_status": "awaiting_outcome",
    }
