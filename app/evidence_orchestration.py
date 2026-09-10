"""Evidence-fed research orchestration boundary.

Validated evidence is distributed to the selected eight active perspectives and
executed through AgentRunner so provider substitution remains explicit and auditable.
No execution, brokerage, credential, or portfolio-mutation capability is introduced.
"""

from typing import Any, Dict, Iterable

from app.agent_registry import active_perspective_ids, build_default_registry
from app.agent_runner import AgentRunner
from app.evidence import validate_evidence
from app.model_provider import ModelProvider


def distribute_evidence(
    evidence: Iterable[Dict[str, Any]],
    agent_ids: Iterable[str],
) -> Dict[str, list[Dict[str, Any]]]:
    """Provide the same validated evidence context to each perspective."""
    items = [dict(item) for item in evidence]
    return {agent_id: list(items) for agent_id in agent_ids}


def run_evidence_fed_agents(
    question: str,
    evidence: Iterable[Dict[str, Any]],
    now=None,
    max_age_seconds: float = 24 * 60 * 60,
    provider: ModelProvider | None = None,
    learning_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run the eight active perspectives using the same validated evidence."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    evidence_list = [dict(item) for item in evidence]
    validation = []
    usable = []
    for item in evidence_list:
        report = validate_evidence(item, now=now, max_age_seconds=max_age_seconds)
        validation.append(report)
        if report["decision_usable"] and item.get("decision_usable", True):
            usable.append(item)

    registry = build_default_registry()
    active_ids = active_perspective_ids()
    evidence_by_agent = distribute_evidence(usable, active_ids)
    runner = AgentRunner(provider)
    agents = [
        runner.run(
            registry.get(agent_id),
            question,
            evidence_by_agent.get(agent_id, []),
            learning_context=learning_context,
        )
        for agent_id in active_ids
    ]

    return {
        "question": question,
        "agent_count": len(agents),
        "active_perspectives": active_ids,
        "registered_agent_count": len(registry.ids()),
        "agents": agents,
        "evidence_count": len(evidence_list),
        "usable_evidence_count": len(usable),
        "blocked_evidence_count": len(evidence_list) - len(usable),
        "validation": validation,
        "provider": runner.provider.name,
        "learning_context_supplied": bool(learning_context),
        "perspectives_share_conclusions": False,
        "research_only": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "human_decision_required": True,
    }
