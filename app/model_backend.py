"""Guarded model backends for AletheiaTelos.

The callable backend remains the generic test seam. The OpenAI Responses backend
is deliberately limited to structured research output. Research context is supplied
separately from evidence and cannot be promoted to evidence by the backend.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agent_contract import Agent
from app.model_provider import ModelProvider, ResearcherOnlyModelProvider


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

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = {
            "question": question,
            "agent": {"agent_id": agent.spec.agent_id, "role": agent.spec.role, "default_horizon": agent.spec.default_horizon, "capability_profile": dict(agent.spec.capability_profile)},
            "evidence": [dict(item) for item in evidence],
            "institutional_learning": dict(learning_context or {}),
            "research_context": dict(research_context or {}),
            "constraints": {"research_only": True, "execution_capability": False, "brokerage_connectivity": False, "portfolio_mutation": False, "human_decision_required": True},
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
    """Backward-compatible provider facade over the callable backend test seam."""

    name = "callable"

    def __init__(self, invoke: Callable[[Mapping[str, Any]], Dict[str, Any]], model_name: str = "unspecified") -> None:
        self.backend = CallableModelBackend(invoke, model_name=model_name)

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self.backend.assess(agent, question, evidence, learning_context=learning_context, research_context=research_context)


_RESEARCH_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "direction": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL", "NO_DATA"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "horizon": {"type": "string"},
        "thesis": {"type": "string"},
        "evidence_basis": {"type": "array", "items": {"type": "string"}},
        "contradictory_evidence_basis": {"type": "array", "items": {"type": "string"}},
        "invalidation_conditions": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["direction", "confidence", "horizon", "thesis", "evidence_basis", "contradictory_evidence_basis", "invalidation_conditions", "assumptions"],
}


class OpenAIResponsesModelBackend:
    """Call one OpenAI Responses model with strict structured research output."""

    name = "openai-responses"

    def __init__(self, api_key: str | None = None, model_name: str | None = None, endpoint: str | None = None, post_json: Callable[[str, Dict[str, Any], Dict[str, str]], Dict[str, Any]] | None = None) -> None:
        self.api_key = api_key or os.getenv("ALETHEIA_MODEL_API_KEY", "").strip()
        self.model_name = (model_name or os.getenv("ALETHEIA_MODEL_NAME", "gpt-5.6-terra")).strip()
        self.endpoint = (endpoint or os.getenv("ALETHEIA_MODEL_ENDPOINT", "https://api.openai.com/v1/responses")).strip()
        self._post_json = post_json or self._default_post_json
        if not self.api_key: raise ModelBackendError("ALETHEIA_MODEL_API_KEY is required for the real model backend.")
        if not self.model_name: raise ModelBackendError("ALETHEIA_MODEL_NAME cannot be empty.")
        if not self.endpoint: raise ModelBackendError("ALETHEIA_MODEL_ENDPOINT cannot be empty.")

    @staticmethod
    def _default_post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=60) as response: return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ModelBackendError(f"model API returned HTTP {exc.code}: {body[:500]}") from exc
        except URLError as exc: raise ModelBackendError(f"model API request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc: raise ModelBackendError("model API returned invalid JSON") from exc

    @staticmethod
    def _extract_structured_output(response: Mapping[str, Any]) -> Dict[str, Any]:
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            try: parsed = json.loads(output_text)
            except json.JSONDecodeError as exc: raise ModelBackendError("model returned non-JSON structured output") from exc
            if isinstance(parsed, dict): return parsed
        for item in response.get("output", []) or []:
            for content in item.get("content", []) or []:
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    try: parsed = json.loads(text)
                    except json.JSONDecodeError as exc: raise ModelBackendError("model returned non-JSON structured output") from exc
                    if isinstance(parsed, dict): return parsed
        raise ModelBackendError("model response contained no structured output")

    @staticmethod
    def _prompt(agent: Agent, question: str, evidence: list[Dict[str, Any]], learning_context: Dict[str, Any], research_context: Dict[str, Any]) -> str:
        if agent.spec.agent_id == "scientist":
            role_prompt = "You are the Scientist perspective in AletheiaTelos. You are a scientific and epistemic validity component, not an investment authority. Ask what would have to be true for this conclusion to be valid, and what evidence could prove it wrong. Use only supplied decision-usable evidence; do not add facts or sources. Treat research context as hypotheses and relationships to test, never as evidence. Distinguish observations from interpretations. Examine causal claims for confounding, reverse causality, selection effects, survivorship bias, measurement artifacts, and alternative explanations. Evaluate evidence quality, representativeness, recency, independence, methodological validity, statistical weakness, model sensitivity, and regime dependence. Identify assumptions, falsification tests, failure modes, unknowns, limitations, and what evidence would change the conclusion. If evidence is insufficient, return NO_DATA with confidence 0. Confidence is not probability. Do not recommend execution, brokerage activity, portfolio mutation, or autonomous action. Preserve human decision authority. Return only the requested structured object."
        elif agent.spec.agent_id == "governance":
            role_prompt = "You are the Governance perspective in AletheiaTelos. You are an independent review and oversight component, not an investment authority and not a decision-maker. Review whether system behavior remains inside the CHARTER and authority boundary. Use only supplied decision-usable evidence; do not add facts or sources. Treat research context as non-evidentiary hypotheses and relationships. Check preservation of human investment authority, research-only operation, prohibition of autonomous execution, brokerage, portfolio mutation, and capital movement, and integrity of evidence validation and provenance. Identify conflicts, unauthorized autonomy, unsupported authority claims, missing escalation, or conditions requiring human review. Do not override perspectives or make an investment decision. If evidence is insufficient, return NO_DATA with confidence 0. Do not fabricate evidence or grant authority. Preserve human decision authority. Return only the requested structured object."
        else:
            role_prompt = "You are the Researcher perspective in AletheiaTelos. You are an evidence-bound research component, not an investment authority. Use only supplied evidence; do not add facts, sources, market data, or claims from outside it. Treat research context as hypotheses and research leads, not evidence. Identify which supplied evidence supports or contradicts the assessment. Use research hypotheses to formulate tests and identify missing evidence, but never cite a hypothesis as evidence. If evidence is insufficient, return NO_DATA with confidence 0. Distinguish observations from interpretation in the thesis. State assumptions and concrete invalidation conditions. Do not recommend execution, brokerage activity, portfolio mutation, or autonomous action. Confidence is not probability. Return only the requested structured object."
        return role_prompt + "\n\n" + f"Question: {question}\nPerspective role: {agent.spec.role}\nDefault horizon: {agent.spec.default_horizon}\nEvidence JSON: {json.dumps(evidence, ensure_ascii=False, sort_keys=True)}\nResearch context JSON (non-evidentiary): {json.dumps(research_context, ensure_ascii=False, sort_keys=True)}\nPrior institutional learning (advisory only): {json.dumps(learning_context, ensure_ascii=False, sort_keys=True)}"

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        evidence_list = [dict(item) for item in evidence]
        if not evidence_list:
            return {"direction": "NO_DATA", "confidence": 0.0, "horizon": agent.spec.default_horizon, "thesis": "No decision-usable evidence was supplied.", "evidence_basis": [], "contradictory_evidence_basis": [], "invalidation_conditions": ["Decision-usable evidence becomes available."], "assumptions": [], "model_version": self.model_name}
        payload = {"model": self.model_name, "input": self._prompt(agent, question, evidence_list, dict(learning_context or {}), dict(research_context or {})), "text": {"format": {"type": "json_schema", "name": "aletheia_researcher_output", "strict": True, "schema": _RESEARCH_OUTPUT_SCHEMA}}}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = self._post_json(self.endpoint, payload, headers)
        if not isinstance(response, dict): raise ModelBackendError("model API response must be an object")
        result = self._extract_structured_output(response)
        allowed_ids = {str(item.get("evidence_id")) for item in evidence_list if item.get("evidence_id")}
        for field in ("evidence_basis", "contradictory_evidence_basis"):
            values = result.get(field)
            if not isinstance(values, list) or not all(str(value) in allowed_ids for value in values): raise ModelBackendError(f"model returned invalid {field}; evidence provenance was not preserved")
        if result.get("direction") != "NO_DATA" and not result["evidence_basis"]: raise ModelBackendError("Active perspective must cite at least one supplied evidence item")
        result["model_version"] = self.model_name
        result["evidence"] = evidence_list
        contradictory_ids = {str(v) for v in result["contradictory_evidence_basis"]}
        result["contradictory_evidence"] = [item for item in evidence_list if str(item.get("evidence_id")) in contradictory_ids]
        return result


class OpenAIResponsesModelProvider(ModelProvider):
    """ModelProvider backed by the single configured OpenAI Responses model."""

    name = "openai-responses"

    def __init__(self, **kwargs: Any) -> None: self.backend = OpenAIResponsesModelBackend(**kwargs)

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self.backend.assess(agent, question, evidence, learning_context=learning_context, research_context=research_context)


def build_default_model_provider() -> ModelProvider:
    """Return real Researcher, Scientist, and Governance routing when configured, otherwise the deterministic path."""
    if not os.getenv("ALETHEIA_MODEL_API_KEY", "").strip():
        from app.model_provider import ContractModelProvider
        return ContractModelProvider()
    model_provider = OpenAIResponsesModelProvider()
    return ResearcherOnlyModelProvider(model_provider, scientist_provider=model_provider, governance_provider=model_provider)
