"""Provider-agnostic agent runner for AletheiaTelos."""

from hashlib import sha256
from typing import Any, Dict, Iterable

from app.agent_contract import Agent
from app.model_provider import ContractModelProvider, ModelProvider
from app.schemas import AgentOutput


class AgentRunner:
    """Run a research agent through a model provider without execution authority."""

    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider or ContractModelProvider()

    @staticmethod
    def _prediction_id(agent_id: str, question: str, model_version: str) -> str:
        material = f"{agent_id}|{model_version}|{question.strip()}".encode("utf-8")
        return f"pred-{sha256(material).hexdigest()[:16]}"

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
        if result.get("predicted_probability") is not None:
            result.setdefault(
                "prediction_id",
                self._prediction_id(agent.spec.agent_id, question, str(result["model_version"])),
            )
        try:
            validated = AgentOutput(**result)
        except Exception as exc:
            raise ValueError(f"Model provider returned invalid AgentOutput: {exc}") from exc

        if hasattr(validated, "model_dump"):
            validated_data = validated.model_dump()
        else:
            validated_data = validated.dict()

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
