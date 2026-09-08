"""Guarded callable model backend for AletheiaTelos.

This module provides the smallest practical bridge from an external model runtime
into the existing provider contract. It intentionally accepts a caller-supplied
callable rather than importing a vendor SDK. The callable has no access to tools
through this boundary; its output is validated by AgentRunner before it can enter the reasoning pipeline.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping

from app.agent_contract import Agent
from app.model_provider import ModelProvider


class ModelBackendError(RuntimeError):
    """Raised when a model backend cannot produce a usable response."""


class CallableModelBackend:
    """Adapt a plain callable into the structured model-provider interface."""

    name = "callable"

    def __init__(self, invoke: Callable[[Mapping[str, Any]], Dict[str, Any]], model_name: str = "unspecified") -> None:
        if not callable(invoke):
            raise TypeError("invoke must be callable")
        self._invoke = invoke
        self.model_name = model_name.strip() or "unspecified"

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
            "constraints": {
                "research_only": True,
                "execution_capability": False,
                "brokerage_connectivity": False,
                "portfolio_mutation": False,
                "human_decision_required": True,
            },
        }
        try:
            result = self._invoke(context)
        except Exception as exc:
            raise ModelBackendError(f"model backend failed: {exc}") from exc
        if not isinstance(result, dict):
            raise ModelBackendError("model backend must return a dictionary")
        result = dict(result)
        result.setdefault("model_version", self.model_name)
        return result


class CallableModelProvider(ModelProvider):
    """ModelProvider implementation backed by a guarded callable."""

    name = "callable-model"

    def __init__(self, invoke: Callable[[Mapping[str, Any]], Dict[str, Any]], model_name: str = "unspecified") -> None:
        self.backend = CallableModelBackend(invoke, model_name=model_name)

    def assess(
        self,
        agent: Agent,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self.backend.assess(agent, question, evidence)
