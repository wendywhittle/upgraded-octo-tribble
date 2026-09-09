"""Canonical Computational Kaleidoscope research roster.

The full registry remains available for compatibility, while Iteration 2A activates
four deliberately differentiated perspectives. No perspective grants execution,
brokerage, credential, or portfolio-mutation capability.
"""

from typing import Any, Dict, Iterable

from app.agent_contract import AgentRegistry, AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner


_ACTIVE_PERSPECTIVES = ("researcher", "quant", "skeptic", "contrarian")

_ROSTER = (
    (
        "researcher",
        "Evidence-Bound Fundamental Research",
        "medium",
        "NEUTRAL",
        0.0,
        "Assess only what can be supported or challenged by the supplied decision-usable evidence.",
        "The supplied evidence may be incomplete, contradictory, stale, or insufficient for a conclusion.",
    ),
    (
        "quant",
        "Quantitative and Statistical Interpretation",
        "medium",
        "LONG",
        0.68,
        "Evaluate whether the supplied evidence supports a quantitatively coherent interpretation.",
        "The apparent relationship may be statistically weak, nonlinear, or sensitive to assumptions.",
    ),
    ("investor", "Investment Thesis", "long", "LONG", 0.76, "Entry valuation may provide an acceptable margin of safety.", "Exit assumptions could be too optimistic."),
    ("scientist", "Scenario Analysis", "medium", "NEUTRAL", 0.61, "The result depends materially on assumptions that require testing.", "Scenario distributions may be wider than expected."),
    ("systems", "Systems Risk", "medium", "SHORT", 0.64, "Interacting macro, financing, and operational risks could compound.", "The system may remain resilient under favorable conditions."),
    (
        "contrarian",
        "Strongest Credible Opposing Case",
        "short",
        "SHORT",
        0.71,
        "Construct the strongest credible case against the prevailing interpretation using the supplied evidence.",
        "The opposing case may rely on an assumption that the evidence does not establish.",
    ),
    (
        "skeptic",
        "Evidence and Assumption Challenge",
        "medium",
        "NEUTRAL",
        0.0,
        "Identify missing evidence, unsupported assumptions, failure conditions, and reasons the apparent thesis could be wrong.",
        "A weakness in the thesis does not by itself establish the opposing thesis.",
    ),
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


def active_perspective_ids() -> list[str]:
    """Return the intentionally small Iteration 2A active perspective set."""
    return list(_ACTIVE_PERSPECTIVES)


def run_default_agents(question: str, evidence_by_agent: Dict[str, Iterable[Dict[str, Any]]] | None = None) -> list[Dict[str, Any]]:
    """Run every registered perspective through the provider-agnostic runner."""
    registry = build_default_registry()
    runner = AgentRunner()
    evidence_by_agent = evidence_by_agent or {agent_id: [] for agent_id, *_ in _ROSTER}
    return [
        runner.run(registry.get(agent_id), question, evidence_by_agent.get(agent_id, []))
        for agent_id in registry.ids()
    ]
