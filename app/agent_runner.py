"""Provider-agnostic agent runner for AletheiaTelos.

The runner is deliberately narrow: validated evidence enters, an Agent contract is
invoked, and a structured research assessment exits. Model/provider implementations
remain replaceable and cannot execute orders, access brokerage, or mutate portfolios.
"""

from typing import Any, Dict, Iterable, Protocol

from app.agent_contract import Agent


class AgentProvider(Protocol):
    """Provider interface for future model-backed agents."""

    name: str

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]: ...


class ContractAgentProvider:
    """Default provider that delegates directly to the formal Agent contract."""

    name = "contract"

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return agent.assess(question, evidence)


class AgentRunner:
    """Execute research agents without granting execution capabilities."""

    def __init__(self, provider: AgentProvider | None = None):
        self.provider = provider or ContractAgentProvider()

    def run(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if agent.spec.capability_profile.get("execute", False):
            raise ValueError("Agent execution capability is prohibited.")
        if agent.spec.capability_profile.get("brokerage", False):
            raise ValueError("Agent brokerage capability is prohibited.")
        if agent.spec.capability_profile.get("portfolio_mutation", False):
            raise ValueError("Agent portfolio mutation is prohibited.")

        result = self.provider.assess(agent, question, evidence)
        result.setdefault("agent_runner", self.__class__.__name__)
        result.setdefault("provider", self.provider.name)
        result["execution_capability"] = False
        result["brokerage_connectivity"] = False
        result["portfolio_mutation"] = False
        result["human_decision_required"] = True
        return result
