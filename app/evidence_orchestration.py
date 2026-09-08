"""Evidence-fed research orchestration boundary.

This module connects already-acquired, integrity-checked evidence to the registered
Computational Kaleidoscope perspectives. It deliberately does not fetch external data,
run the risk engine, synthesize investment decisions, or execute anything.
"""

from typing import Any, Dict, Iterable

from app.agent_registry import build_default_registry
from app.evidence import validate_evidence


def distribute_evidence(
    evidence: Iterable[Dict[str, Any]],
    agent_ids: Iterable[str],
) -> Dict[str, list[Dict[str, Any]]]:
    """Provide the same evidence context to each perspective after integrity validation.

    Invalid evidence is retained in the audit result but never passed to agents.
    """
    items = [dict(item) for item in evidence]
    return {agent_id: list(items) for agent_id in agent_ids}


def run_evidence_fed_agents(
    question: str,
    evidence: Iterable[Dict[str, Any]],
    now=None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Run the canonical roster using only evidence that passes integrity checks."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    evidence_list = [dict(item) for item in evidence]
    validation = [
        validate_evidence(item, now=now, max_age_seconds=max_age_seconds)
        for item in evidence_list
    ]
    usable = [
        item for item, report in zip(evidence_list, validation)
        if report["decision_usable"]
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
