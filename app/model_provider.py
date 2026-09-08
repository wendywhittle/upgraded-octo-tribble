"""Structured model-provider contract for AletheiaTelos.

This module defines the shape of model-backed research context without binding the
system to a specific vendor SDK. Providers remain downstream of evidence integrity
and upstream of conflict, risk, skepticism, synthesis, and governance.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Protocol


@dataclass(frozen=True)
class ResearchContext:
    agent_id: str
    role: str
    horizon: str
    question: str
    evidence: tuple[Dict[str, Any], ...]

    @classmethod
    def build(
        cls,
        agent_id: str,
        role: str,
        horizon: str,
        question: str,
        evidence: Iterable[Mapping[str, Any]],
    ) -> "ResearchContext":
        return cls(
            agent_id=agent_id,
            role=role,
            horizon=horizon,
            question=question,
            evidence=tuple(dict(item) for item in evidence),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "horizon": self.horizon,
            "question": self.question,
            "evidence": [dict(item) for item in self.evidence],
        }


class StructuredModel(Protocol):
    name: str

    def assess(self, context: ResearchContext) -> Mapping[str, Any]: ...
