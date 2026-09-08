"""Provider-agnostic agent runner for AletheiaTelos.

Providers may supply model-backed assessments, but the runner remains a hard
research-only boundary. Provider output is normalized and capability flags are
reasserted by the runner rather than trusted from the provider.
"""

from typing import Any, Dict, Iterable, Protocol

from app.agent_contract import Agent


class AgentProvider(Protocol):
    name: str

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]: ...


class ContractAgentProvider:
    """Default deterministic provider backed by the formal Agent contract."""

    name = "contract"

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        return agent.assess(question, evidence)


class CallableModelProvider:
    """Adapter for a caller-owned model function.

    The callable receives only structured research context. It has no broker,
    order, credential, or portfolio interface through this adapter.
    """

    def __init__(self, model_callable, name: str = "callable-model"):
        if not callable(model_callable):
            raise TypeError("model_callable must be callable")
        if not name.strip():
            raise ValueError("Provider name must not be empty")
        self.model_callable = model_callable
        self.name = name

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        evidence_list = [dict(item) for item in evidence]
        result = self.model_callable(
            {
                "agent_id": agent.spec.agent_id,
                "role": agent.spec.role,
                "horizon": agent.spec.default_horizon,
                "question": question,
                "evidence": evidence_list,
            }
        )
        if not isinstance(result, dict):
            raise TypeError("Model provider must return a dictionary")
        return dict(result)


class AgentRunner:
    """Run an agent through a provider without granting execution capabilities."""

    def __init__(self, provider: AgentProvider | None = None):
        self.provider = provider or ContractAgentProvider()

    def run(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
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
