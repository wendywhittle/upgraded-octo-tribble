"""Provider-agnostic agent runner for AletheiaTelos."""

from typing import Any, Dict, Iterable

from app.agent_contract import Agent
from app.model_provider import ContractModelProvider, ModelProvider


class AgentRunner:
    """Run a research agent through a model provider without execution authority."""

    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider or ContractModelProvider()

    def run(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        capabilities = agent.spec.capability_profile
        if capabilities.get("execute", False):
            raise ValueError("Agent execution capability is prohibited.")
        if capabilities.get("brokerage", False):
            raise ValueError("Agent brokerage capability is prohibited.")
        if capabilities.get("portfolio_mutation", False):
            raise ValueError("Agent portfolio mutation is prohibited.")

        result = self.provider.assess(
            agent_id=agent.spec.agent_id,
            role=agent.spec.role,
            question=question,
            evidence=evidence,
        )
        if not isinstance(result, dict):
            raise ValueError("Model provider must return a dictionary.")
        result = dict(result)
        result.setdefault("agent_id", agent.spec.agent_id)
        result.setdefault("role", agent.spec.role)
        result["agent_runner"] = self.__class__.__name__
        result["provider"] = self.provider.name
        result["execution_capability"] = False
        result["brokerage_connectivity"] = False
        result["portfolio_mutation"] = False
        result["human_decision_required"] = True
        return result
