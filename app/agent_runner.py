"""Provider-agnostic agent runner for AletheiaTelos."""

from typing import Any, Dict, Iterable

from app.agent_contract import Agent
from app.model_provider import ContractModelProvider, ModelProvider
from app.schemas import AgentOutput


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

        result = self.provider.assess(agent, question, evidence)
        if not isinstance(result, dict):
            raise ValueError("Model provider must return a dictionary.")
        result = dict(result)
        result.setdefault("agent_id", agent.spec.agent_id)
        result.setdefault("strategy", agent.spec.role)
        result.setdefault("horizon", agent.spec.default_horizon)
        result.setdefault("model_version", f"{self.provider.name}-provider")
        result.setdefault("evidence", [])
        result.setdefault("assumptions", [])
        result.setdefault("invalidation_conditions", [])
        try:
            validated = AgentOutput(**result)
        except Exception as exc:
            raise ValueError(f"Model provider returned invalid AgentOutput: {exc}") from exc

        if hasattr(validated, "model_dump"):
            validated_data = validated.model_dump()
        else:
            validated_data = validated.dict()

        # Keep useful provider metadata while making the validated AgentOutput canonical.
        output = dict(result)
        output.update(validated_data)
        output["capability_profile"] = dict(capabilities)
        output["agent_runner"] = self.__class__.__name__
        output["provider"] = self.provider.name
        output["execution_capability"] = False
        output["brokerage_connectivity"] = False
        output["portfolio_mutation"] = False
        output["human_decision_required"] = True
        return output
