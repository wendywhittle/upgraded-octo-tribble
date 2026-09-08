"""Research-to-reasoning boundary for AletheiaTelos.

Evidence is supplied to an agent as inspectable context; this module does not
fetch data, execute trades, or manufacture certainty. Agents may produce a
research assessment, but downstream simulation and governance remain separate.
"""

from typing import Any, Dict, Iterable


def build_reasoning_context(evidence: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a compact, provenance-preserving context from decision-usable evidence."""
    usable = []
    blocked = []
    for item in evidence:
        if item.get("decision_usable", True):
            usable.append(item)
        else:
            blocked.append(item)
    return {
        "evidence_count": len(usable),
        "blocked_evidence_count": len(blocked),
        "evidence": usable,
        "reasoning_applied": False,
        "execution_capability": False,
        "brokerage_connectivity": False,
    }


def reason_from_evidence(
    agent_id: str,
    question: str,
    evidence: Iterable[Dict[str, Any]],
    thesis: str,
    direction: str = "NEUTRAL",
    confidence: float = 0.0,
    horizon: str = "medium",
) -> Dict[str, Any]:
    """Create an explicitly labeled research assessment from supplied evidence.

    This function is intentionally deterministic and provider-agnostic. It does
    not call a model or decide whether capital should be deployed.
    """
    if not agent_id.strip() or not question.strip() or not thesis.strip():
        raise ValueError("agent_id, question, and thesis are required.")
    if direction not in {"LONG", "SHORT", "NEUTRAL", "NO_DATA"}:
        raise ValueError("Unsupported direction.")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence must be between 0 and 1.")

    context = build_reasoning_context(evidence)
    if not context["evidence"]:
        direction = "NO_DATA"
        confidence = 0.0

    return {
        "agent_id": agent_id,
        "question": question,
        "direction": direction,
        "confidence": confidence,
        "horizon": horizon,
        "thesis": thesis,
        "evidence": context["evidence"],
        "blocked_evidence_count": context["blocked_evidence_count"],
        "reasoning_applied": True,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "human_decision_required": True,
    }
