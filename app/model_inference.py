"""Structured model-inference boundary for AletheiaTelos.

This adapter deliberately contains no vendor SDK, credentials, network access, or
execution capability. A caller supplies a callable model backend; the adapter gives
it a structured research context and returns its structured assessment unchanged.
AgentRunner remains responsible for AgentOutput validation and capability limits.
"""

from typing import Any, Callable, Dict, Iterable, Protocol

from app.agent_contract import Agent


class ModelInvoker(Protocol):
    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]: ...


class CallableModelProvider:
    """Adapt an injected model callable to the AletheiaTelos provider contract."""

    name = "injected-model"

    def __init__(self, invoke: ModelInvoker, name: str = "injected-model"):
        if not callable(invoke):
            raise TypeError("Model invoker must be callable.")
        if not name.strip():
            raise ValueError("Model provider name cannot be empty.")
        self.invoke = invoke
        self.name = name.strip()

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        context = {
            "question": question,
            "agent": {
                "agent_id": agent.spec.agent_id,
                "role": agent.spec.role,
                "default_horizon": agent.spec.default_horizon,
                "capability_profile": dict(agent.spec.capability_profile),
            },
            "evidence": [dict(item) for item in evidence],
            "instructions": {
                "task": "Produce a research assessment for the assigned perspective.",
                "output_contract": "AgentOutput",
                "research_only": True,
                "human_decision_required": True,
                "execution_allowed": False,
                "brokerage_allowed": False,
                "portfolio_mutation_allowed": False,
            },
        }
        result = self.invoke(context)
        if not isinstance(result, dict):
            raise ValueError("Model invoker must return a dictionary.")
        return dict(result)
