"""Adversarial review of CRE simulation outputs.

This module reviews distributions and explicit assumptions. It does not alter the
simulation or grant authority to invest.
"""
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CREAdversarialReview:
    status: str
    challenges: Sequence[str] = field(default_factory=tuple)
    dominant_risks: Sequence[str] = field(default_factory=tuple)
    unresolved_questions: Sequence[str] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    human_decision_required: bool = True


def review_cre_simulation(simulation: Mapping[str, Any], assumptions: Sequence[str] = (), evidence_ids: Sequence[str] = ()) -> CREAdversarialReview:
    """Challenge simulation outputs without changing their results."""
    challenges: list[str] = []
    risks: list[str] = []
    scenarios = simulation.get("scenarios", [])
    for scenario in scenarios:
        name = str(scenario.get("scenario", "")).lower()
        loss = scenario.get("probability_loss")
        drawdown = scenario.get("max_drawdown_mean")
        if loss is not None and loss > 0:
            challenges.append(f"{scenario.get('scenario')}: probability of loss is {loss:.2%}.")
            risks.append(f"loss risk in {scenario.get('scenario')}")
        if drawdown is not None and drawdown > 0.2:
            challenges.append(f"{scenario.get('scenario')}: mean maximum drawdown exceeds 20%.")
            risks.append(f"drawdown in {scenario.get('scenario')}")
        if name in {"bear", "adversarial", "tail risk", "tail_risk"} and (loss or 0) > 0.25:
            challenges.append(f"{scenario.get('scenario')}: adverse distribution warrants explicit capital-preservation review.")
    if not scenarios:
        challenges.append("No simulation scenarios were available for adversarial review.")
    if not assumptions:
        challenges.append("No explicit CRE assumptions were supplied to challenge.")
    questions = [
        "What breaks first under the adverse distribution?",
        "Which assumption contributes most to downside?",
        "What happens if financing becomes more expensive or occupancy falls?",
        "What evidence would invalidate the thesis?",
    ]
    return CREAdversarialReview(
        status="reviewed" if scenarios else "insufficient_data",
        challenges=tuple(challenges),
        dominant_risks=tuple(dict.fromkeys(risks)),
        unresolved_questions=tuple(questions),
        evidence_ids=tuple(evidence_ids),
    )
