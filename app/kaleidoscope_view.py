"""Read-only observability projection for the Computational Kaleidoscope."""

from __future__ import annotations

from typing import Any, Dict, Iterable


PERSPECTIVES = (
    "researcher", "quant", "investor", "scientist", "systems",
    "contrarian", "philosopher", "observer", "meta_intelligence", "governance",
)


def build_kaleidoscope_view(
    agents: Iterable[Dict[str, Any]],
    evidence: Dict[str, Any] | None = None,
    conflicts: Iterable[Dict[str, Any]] = (),
    horizon_divergences: Iterable[Dict[str, Any]] = (),
    simulation: Dict[str, Any] | None = None,
    skeptic: Dict[str, Any] | None = None,
    synthesis: Dict[str, Any] | None = None,
    observer: Dict[str, Any] | None = None,
    governance: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Project analysis state into a UI-safe, read-only view.

    This function does not score, average, authorize, trade, or mutate state.
    """
    agent_list = [dict(agent) for agent in agents]
    cards = [
        {
            "agent_id": agent.get("agent_id"),
            "role": agent.get("role"),
            "direction": agent.get("direction"),
            "confidence": agent.get("confidence", 0.0),
            "horizon": agent.get("horizon"),
            "evidence_count": len(agent.get("evidence", []) or []),
            "model_version": agent.get("model_version"),
        }
        for agent in agent_list
    ]
    return {
        "perspectives": cards,
        "perspective_count": len(cards),
        "expected_perspective_count": len(PERSPECTIVES),
        "evidence": evidence or {},
        "conflicts": list(conflicts),
        "horizon_divergences": list(horizon_divergences),
        "simulation": simulation or {},
        "skeptic": skeptic or {},
        "synthesis": synthesis or {},
        "observer": observer or {},
        "governance": governance or {
            "human_decision_required": True,
            "autonomous_execution": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
        },
        "read_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "human_decision_required": True,
    }
