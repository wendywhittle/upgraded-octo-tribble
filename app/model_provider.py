"""Provider boundary for model-backed AletheiaTelos reasoning.

Providers receive a question, an agent role, and already validated evidence. They
return structured research output. Providers never receive execution, brokerage,
credential, or portfolio-mutation capabilities.
"""

from typing import Any, Dict, Iterable, Protocol


class ModelProvider(Protocol):
    """Minimal interface implemented by any trusted model backend."""

    name: str

    def assess(
        self,
        *,
        agent_id: str,
        role: str,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]: ...


class ContractModelProvider:
    """Deterministic fallback proving the provider boundary without an API call."""

    name = "contract"

    def assess(
        self,
        *,
        agent_id: str,
        role: str,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        items = list(evidence)
        return {
            "agent_id": agent_id,
            "role": role,
            "question": question,
            "evidence": items,
            "direction": "NO_DATA" if not items else "NEUTRAL",
            "confidence": 0.0 if not items else 0.1,
            "thesis": "Insufficient evidence for a directional conclusion." if not items else "Evidence received; further model-specific analysis is required.",
            "horizon": "medium",
            "assumptions": ["Provider output is research-only and depends on supplied evidence."],
            "invalidation_conditions": ["Material evidence contradicts the assessment."],
        }
