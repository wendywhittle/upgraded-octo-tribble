"""Read-only observability projection for the Computational Kaleidoscope."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable

from app.agent_registry import active_perspective_ids


def _assessment_dict(item: Any) -> Dict[str, Any]:
    """Normalize mapping or dataclass assessments without changing their content."""
    if is_dataclass(item):
        return asdict(item)
    return dict(item)


def build_kaleidoscope_view(
    agents: Iterable[Dict[str, Any]],
    evidence: Dict[str, Any] | None = None,
    conflicts: Iterable[Dict[str, Any]] = (),
    horizon_divergences: Iterable[Dict[str, Any]] = (),
    simulation: Dict[str, Any] | None = None,
    skeptic: Dict[str, Any] | None = None,
    meta_intelligence: Dict[str, Any] | None = None,
    synthesis: Dict[str, Any] | None = None,
    observer: Dict[str, Any] | None = None,
    governance: Dict[str, Any] | None = None,
    cre_assessments: Iterable[Any] = (),
) -> Dict[str, Any]:
    """Project analysis state into a UI-safe, read-only view.

    CRE assessments are carried as inspectable records; this projection does not
    score, average, authorize, trade, or mutate state.
    """
    agent_list = [dict(agent) for agent in agents]
    cards = [
        {
            "agent_id": agent.get("agent_id"),
            "role": agent.get("strategy"),
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
        "cre_perspective_assessments": [_assessment_dict(item) for item in cre_assessments],
        "perspective_count": len(cards),
        "expected_perspective_count": len(active_perspective_ids()),
        "evidence": evidence or {},
        "conflicts": list(conflicts),
        "horizon_divergences": list(horizon_divergences),
        "simulation": simulation or {},
        "skeptic": skeptic or {},
        "meta_intelligence": meta_intelligence or {},
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
