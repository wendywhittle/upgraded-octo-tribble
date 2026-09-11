"""Provider-agnostic agent runner for AletheiaTelos."""

from hashlib import sha256
from typing import Any, Dict, Iterable

from app.agent_contract import Agent
from app.epistemic_adapter import prediction_to_epistemic_records, serialize_record
from app.model_provider import ModelProvider
from app.schemas import AgentOutput


class AgentRunner:
    """Run a research agent through a model provider without execution authority."""

    def __init__(self, provider: ModelProvider | None = None):
        if provider is None:
            from app.model_backend import build_default_model_provider
            provider = build_default_model_provider()
        self.provider = provider

    @staticmethod
    def _prediction_id(agent_id: str, question: str, model_version: str, evidence: Iterable[Dict[str, Any]]) -> str:
        evidence_ids = sorted(str(item.get("evidence_id")) for item in evidence if item.get("evidence_id"))
        material = f"{agent_id}|{model_version}|{question.strip()}|{','.join(evidence_ids)}".encode("utf-8")
        return f"pred-{sha256(material).hexdigest()[:16]}"

    def run(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        capabilities = agent.spec.capability_profile
        if capabilities.get("execute", False):
            raise ValueError("Agent execution capability is prohibited.")
        if capabilities.get("brokerage", False):
            raise ValueError("Agent brokerage capability is prohibited.")
        if capabilities.get("portfolio_mutation", False):
            raise ValueError("Agent portfolio mutation capability is prohibited.")

        evidence_list = [dict(item) for item in evidence]
        if learning_context is None:
            result = self.provider.assess(agent, question, evidence_list)
        else:
            result = self.provider.assess(agent, question, evidence_list, learning_context=learning_context)
        if not isinstance(result, dict):
            raise ValueError("Model provider must return a dictionary.")
        result = dict(result)

        if result.get("agent_id", agent.spec.agent_id) != agent.spec.agent_id:
            raise ValueError("Model provider returned an AgentOutput for the wrong agent.")
        for forbidden in ("execution_capability", "brokerage_connectivity", "portfolio_mutation"):
            if result.get(forbidden) is True:
                raise ValueError(f"Model provider attempted to enable prohibited capability: {forbidden}.")
        if result.get("human_decision_required") is False:
            raise ValueError("Model provider attempted to remove human decision authority.")

        result["agent_id"] = agent.spec.agent_id
        result.setdefault("strategy", agent.spec.role)
        result.setdefault("horizon", agent.spec.default_horizon)
        result.setdefault("model_version", f"{self.provider.name}-provider")
        result["evidence"] = evidence_list
        result.setdefault("assumptions", [])
        result.setdefault("invalidation_conditions", [])
        if result.get("predicted_probability") is not None:
            result.setdefault("prediction_id", self._prediction_id(agent.spec.agent_id, question, str(result["model_version"]), evidence_list))

        try:
            validated = AgentOutput(**result)
        except Exception as exc:
            raise ValueError(f"Model provider returned invalid AgentOutput: {exc}") from exc

        validated_data = validated.model_dump() if hasattr(validated, "model_dump") else validated.dict()
        output = dict(result)
        output.update(validated_data)
        output["capability_profile"] = dict(capabilities)
        output["agent_runner"] = self.__class__.__name__
        output["provider"] = self.provider.name
        output["learning_context_used"] = bool(learning_context)
        output["execution_capability"] = False
        output["brokerage_connectivity"] = False
        output["portfolio_mutation"] = False
        output["human_decision_required"] = True
        output["epistemic_memory"] = [serialize_record(record) for record in prediction_to_epistemic_records(output)]
        return output
