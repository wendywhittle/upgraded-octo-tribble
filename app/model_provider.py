"""Provider boundary for model-backed AletheiaTelos reasoning.

Providers may change how an Agent's reasoning is produced, but they cannot widen
the Agent's capability profile. The deterministic contract provider remains the
regression path; Iteration 1 selectively routes only Researcher to the configured
real model.
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
        learning_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]: ...


class ContractModelProvider:
    """Reference provider that delegates to the formal Agent contract."""

    name = "contract"

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
        learning_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        # Deterministic contract agents do not consume learned guidance, but the
        # boundary accepts it so model-backed providers can reason over it.
        return agent.assess(question, evidence)


class ResearcherOnlyModelProvider:
    """Use a real model for Researcher and deterministic contract reasoning elsewhere."""

    name = "researcher-selective"

    def __init__(self, researcher_provider: ModelProvider, fallback: ModelProvider | None = None) -> None:
        self.researcher_provider = researcher_provider
        self.fallback = fallback or ContractModelProvider()

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
        learning_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        provider = self.researcher_provider if agent.spec.agent_id == "researcher" else self.fallback
        return provider.assess(agent, question, evidence, learning_context=learning_context)
