"""Canonical Computational Kaleidoscope research roster.

This registry defines perspectives and their research mandates. It grants no execution,
brokerage, credential, or portfolio-mutation capability.
"""

from typing import Any, Dict, Iterable

from app.agent_contract import AgentRegistry, AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner


_ROSTER = (
    ("researcher", "Fundamental Research", "medium", "LONG", 0.72, "The opportunity appears fundamentally supportable pending diligence.", "Asset-level assumptions may be overstated."),
    ("quant", "Quantitative Underwriting", "medium", "LONG", 0.68, "The modeled return profile appears attractive under the base case.", "Downside sensitivity may be nonlinear."),
    ("investor", "Investment Thesis", "long", "LONG", 0.76, "Entry valuation may provide an acceptable margin of safety.", "Exit assumptions could be too optimistic."),
    ("scientist", "Scenario Analysis", "medium", "NEUTRAL", 0.61, "The result depends materially on assumptions that require testing.", "Scenario distributions may be wider than expected."),
    ("systems", "Systems Risk", "medium", "SHORT", 0.64, "Interacting macro, financing, and operational risks could compound.", "The system may remain resilient under favorable conditions."),
    ("contrarian", "Adversarial Challenge", "short", "SHORT", 0.71, "The consensus case may be underestimating a failure mode.", "The identified risk may ultimately prove immaterial."),
    ("philosopher", "Epistemic Analysis", "long", "NEUTRAL", 0.58, "The quality of the decision depends on recognizing what is not known.", "Uncertainty itself may be difficult to quantify."),
    ("observer", "Outcome Observation", "long", "NEUTRAL", 0.55, "The current state should be treated as a baseline for future attribution.", "Future outcomes may not cleanly identify causal drivers."),
    ("meta_intelligence", "Meta-Intelligence", "medium", "NEUTRAL", 0.67, "The disagreement between bullish and defensive perspectives is decision-relevant.", "Some disagreement may arise from different assumptions rather than true conflict."),
    ("governance", "CHARTER", "all", "NEUTRAL", 0.95, "Human Investment Committee authority remains mandatory.", "No autonomous investment authority is permitted."),
)


def build_default_registry() -> AgentRegistry:
    return AgentRegistry(
        DeterministicAgent(
            spec=AgentSpec(agent_id, role, horizon),
            direction=direction,
            confidence=confidence,
            thesis=thesis,
            contradictory_claim=contradictory,
        )
        for agent_id, role, horizon, direction, confidence, thesis, contradictory in _ROSTER
    )


def run_default_agents(
    question: str,
    evidence_by_agent: Dict[str, Iterable[Dict[str, Any]]] | None = None,
) -> list[Dict[str, Any]]:
    """Run every registered perspective through the provider-agnostic runner."""
    registry = build_default_registry()
    runner = AgentRunner()
    evidence_by_agent = evidence_by_agent or {agent_id: [] for agent_id, *_ in _ROSTER}
    return [
        runner.run(registry.get(agent_id), question, evidence_by_agent.get(agent_id, []))
        for agent_id in registry.ids()
    ]
