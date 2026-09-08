"""Evidence-fed research orchestration boundary.

This module connects already-acquired, integrity-checked evidence to the registered
Computational Kaleidoscope perspectives. It deliberately does not fetch external data,
run the risk engine, synthesize investment decisions, or execute anything.
"""

from typing import Any, Dict, Iterable

from app.agent_registry import build_default_registry
from app.evidence import validate_agent_evidence


def distribute_evidence(
    evidence: Iterable[Dict[str, Any]],
    agent_ids: Iterable[str],
) -> Dict[str, list[Dict[str, Any]]]:
    """Provide the same validated evidence context to each perspective.

    The current distribution is intentionally transparent: no hidden agent-specific
    filtering or weighting is performed. Future specialization may narrow context,
    but must remain explicit and auditable.
    """
    items = [dict(item) for item in evidence]
    return {agent_id: list(items) for agent_id in agent_ids}


def run_evidence_fed_agents(
    question: str,
    evidence: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run the canonical roster using only evidence supplied to this boundary."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    evidence_list = [dict(item) for item in evidence]
    validation = [validate_agent_evidence(evidence_list)] if evidence_list else []
    usable = [
        item
        for item in evidence_list
        if item.get("decision_usable", True)
    ]

    registry = build_default_registry()
    evidence_by_agent = distribute_evidence(usable, registry.ids())
    agents = registry.run_all(question, evidence_by_agent)

    return {
        "question": question,
        "agent_count": len(agents),
        "agents": agents,
        "evidence_count": len(evidence_list),
        "usable_evidence_count": len(usable),
        "validation": validation,
        "research_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "human_decision_required": True,
    }
