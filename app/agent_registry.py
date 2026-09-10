"""Canonical Computational Kaleidoscope research roster.

The registry distinguishes directional reasoning perspectives from Meta-Intelligence,
which evaluates the reasoning process rather than voting on direction. No perspective
grants execution, brokerage, credential, or portfolio-mutation capability.
"""

from typing import Any, Dict, Iterable

from app.agent_contract import AgentRegistry, AgentSpec, DeterministicAgent
from app.agent_runner import AgentRunner


_ACTIVE_PERSPECTIVES = ("researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance", "meta_intelligence")
_REASONING_PERSPECTIVES = tuple(agent_id for agent_id in _ACTIVE_PERSPECTIVES if agent_id != "meta_intelligence")

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
    (
        "scientist",
        "Scientific and Epistemic Validity",
        "medium",
        "NEUTRAL",
        0.61,
        "Test whether the conclusion is supported by valid observations, defensible assumptions, and falsifiable reasoning.",
        "The conclusion may depend on confounding, methodological weakness, alternative explanations, or assumptions that have not been tested.",
    ),
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
    ("meta_intelligence", "Meta-Intelligence", "medium", "NEUTRAL", 0.67, "Evaluate whether the reasoning system is behaving reliably across perspectives.", "Apparent agreement may reflect shared evidence, assumptions, or other correlated reasoning."),
    (
        "governance",
        "CHARTER and Authority Boundary",
        "all",
        "NEUTRAL",
        0.95,
        "Verify that system behavior remains within the CHARTER, preserves human investment authority, and requires escalation when governance boundaries are threatened.",
        "A governance violation, unauthorized autonomy, or unsupported authority claim may require immediate human review.",
    ),
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
    """Return all active Computational Kaleidoscope perspectives."""
    return list(_ACTIVE_PERSPECTIVES)


def reasoning_perspective_ids() -> list[str]:
    """Return directional/evidence-fed perspectives, excluding process-level Meta-Intelligence."""
    return list(_REASONING_PERSPECTIVES)


def run_default_agents(question: str, evidence_by_agent: Dict[str, Iterable[Dict[str, Any]]] | None = None) -> list[Dict[str, Any]]:
    """Run registered directional perspectives through the provider-agnostic runner."""
    registry = build_default_registry()
    runner = AgentRunner()
    evidence_by_agent = evidence_by_agent or {agent_id: [] for agent_id in _REASONING_PERSPECTIVES}
    return [
        runner.run(registry.get(agent_id), question, evidence_by_agent.get(agent_id, []))
        for agent_id in _REASONING_PERSPECTIVES
    ]
