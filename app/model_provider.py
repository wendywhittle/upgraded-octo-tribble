"""Provider boundary for model-backed AletheiaTelos reasoning.

A provider may change how an Agent's reasoning is produced, but it cannot widen
the Agent's capability profile. The default implementation delegates to the
existing Agent contract, keeping the system deterministic until a real model
backend is deliberately introduced.
"""

from typing import Any, Dict, Iterable, Protocol

from app.agent_contract import Agent


class ModelProvider(Protocol):
    """Interface for replaceable model/reasoning backends."""

    name: str

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]: ...


class ContractModelProvider:
    """Reference provider that delegates to the formal Agent contract."""

    name = "contract"

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return agent.assess(question, evidence)
