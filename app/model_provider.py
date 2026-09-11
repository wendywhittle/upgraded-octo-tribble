"""Provider boundary for model-backed AletheiaTelos reasoning.

Providers may change how an Agent's reasoning is produced, but they cannot widen
the Agent's capability profile. Research context is passed separately from evidence
so hypotheses and relationships can inform testing without becoming facts.
"""

from typing import Any, Dict, Iterable, Protocol

from app.agent_contract import Agent


class ModelProvider(Protocol):
    name: str
    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]: ...


class ContractModelProvider:
    name = "contract"
    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return agent.assess(question, evidence)


class ResearcherOnlyModelProvider:
    """Use a real model for Researcher, Scientist, and Governance; fall back deterministically for others."""
    name = "researcher-scientist-governance-selective"

    def __init__(self, researcher_provider: ModelProvider, fallback: ModelProvider | None = None, *, scientist_provider: ModelProvider | None = None, governance_provider: ModelProvider | None = None) -> None:
        self.researcher_provider = researcher_provider
        self.scientist_provider = scientist_provider or researcher_provider
        self.governance_provider = governance_provider or researcher_provider
        self.fallback = fallback or ContractModelProvider()

    def assess(self, agent: Agent, question: str, evidence: Iterable[Dict[str, Any]], learning_context: Dict[str, Any] | None = None, research_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if agent.spec.agent_id == "researcher": provider = self.researcher_provider
        elif agent.spec.agent_id == "scientist": provider = self.scientist_provider
        elif agent.spec.agent_id == "governance": provider = self.governance_provider
        else: provider = self.fallback
        if research_context is None:
            return provider.assess(agent, question, evidence, learning_context=learning_context)
        return provider.assess(agent, question, evidence, learning_context=learning_context, research_context=research_context)
