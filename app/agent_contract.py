"""Formal agent contract for AletheiaTelos.

Agents are research components: they may inspect supplied evidence and return an
assessment, but they have no execution, brokerage, credential, or portfolio
mutation capability. The contract keeps agent reasoning structurally separate
from risk simulation, skepticism, synthesis, and governance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Protocol

from app.reasoning import reason_from_evidence
from app.schemas import Direction


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: str
    default_horizon: str
    capability_profile: Dict[str, bool] = field(
        default_factory=lambda: {
            "read_evidence": True,
            "reason": True,
            "execute": False,
            "brokerage": False,
            "portfolio_mutation": False,
        }
    )


class Agent(Protocol):
    spec: AgentSpec

    def assess(
        self,
        question: str,
        evidence: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]: ...


@dataclass
class DeterministicAgent:
    spec: AgentSpec
    direction: Direction = "NEUTRAL"
    confidence: float = 0.0
    thesis: str = ""
    contradictory_claim: str = ""

    def assess(self, question: str, evidence: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        evidence_list = list(evidence)
        result = reason_from_evidence(
            agent_id=self.spec.agent_id,
            question=question,
            evidence=evidence_list,
            thesis=self.thesis,
            direction=self.direction,
            confidence=self.confidence,
            horizon=self.spec.default_horizon,
        )
        result.update(
            {
                "strategy": self.spec.role,
                "model_version": "deterministic-agent-1.0",
                "invalidation_conditions": ["Material evidence contradicts the core thesis."],
                "assumptions": ["Assessment is dependent on supplied evidence."],
                "evidence_basis": [str(item["evidence_id"]) for item in evidence_list if item.get("evidence_id")],
                "capability_profile": dict(self.spec.capability_profile),
            }
        )
        if self.contradictory_claim:
            # This is explicitly agent-generated challenge text, not supplied evidence.
            result["contradictory_evidence"] = [
                {
                    "evidence_id": f"{self.spec.agent_id}-challenge",
                    "source": "agent challenge",
                    "claim": self.contradictory_claim,
                    "provenance": {"type": "agent_generated", "independent": False},
                }
            ]
        return result


class AgentRegistry:
    """Registry that enforces the research-only agent capability profile."""

    def __init__(self, agents: Iterable[Agent]):
        self._agents: Dict[str, Agent] = {}
        for agent in agents:
            if agent.spec.agent_id in self._agents:
                raise ValueError(f"Duplicate agent_id: {agent.spec.agent_id}")
            if agent.spec.capability_profile.get("execute", False):
                raise ValueError("Agent execution capability is prohibited.")
            if agent.spec.capability_profile.get("brokerage", False):
                raise ValueError("Agent brokerage capability is prohibited.")
            if agent.spec.capability_profile.get("portfolio_mutation", False):
                raise ValueError("Agent portfolio mutation is prohibited.")
            self._agents[agent.spec.agent_id] = agent

    def get(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent_id: {agent_id}") from exc

    def run_all(
        self,
        question: str,
        evidence_by_agent: Dict[str, Iterable[Dict[str, Any]]],
    ) -> list[Dict[str, Any]]:
        return [
            self._agents[agent_id].assess(question, evidence_by_agent.get(agent_id, []))
            for agent_id in self._agents
        ]

    def ids(self) -> list[str]:
        return list(self._agents)
