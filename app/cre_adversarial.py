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
    """Challenge actual simulation distributions and explicit CRE assumptions."""
    challenges: list[str] = []
    risks: list[str] = []
    scenarios = simulation.get("scenarios", [])
    worst = None
    for scenario in scenarios:
        name = str(scenario.get("scenario", ""))
        loss = scenario.get("probability_loss")
        drawdown = scenario.get("max_drawdown_mean")
        dscr = scenario.get("mean_dscr")
        outcome = scenario.get("mean_equity_outcome")
        if worst is None or (outcome is not None and outcome < worst.get("mean_equity_outcome", float("inf"))):
            worst = scenario
        if loss is not None and loss > 0:
            challenges.append(f"{name}: probability of loss is {loss:.2%}.")
            risks.append(f"loss risk in {name}")
        if drawdown is not None and drawdown > 0.2:
            challenges.append(f"{name}: mean maximum equity drawdown exceeds 20% ({drawdown:.2%}).")
            risks.append(f"drawdown in {name}")
        if dscr is not None and dscr < 1.0:
            challenges.append(f"{name}: modeled DSCR falls below 1.00x ({dscr:.2f}x).")
            risks.append(f"debt-service coverage in {name}")
        if name.upper() in {"BEAR", "ADVERSARIAL", "TAIL RISK"} and loss is not None and loss > 0.25:
            challenges.append(f"{name}: adverse distribution warrants explicit capital-preservation review.")
    if worst is not None and worst.get("mean_equity_outcome") is not None:
        challenges.append(f"Worst modeled scenario is {worst.get('scenario')} with mean equity outcome {worst.get('mean_equity_outcome'):,.0f}.")
    inputs = simulation.get("inputs", {})
    if inputs:
        if inputs.get("interest_rate") is not None:
            challenges.append(f"Financing is explicitly modeled at {inputs['interest_rate']:.2%}; rate sensitivity should be tested independently.")
        if inputs.get("loan_to_value") is not None:
            challenges.append(f"Leverage is explicitly modeled at {inputs['loan_to_value']:.2%} LTV.")
        if inputs.get("occupancy") is not None:
            challenges.append(f"Occupancy input is {inputs['occupancy']:.2%}; downside occupancy should be tested.")
        if inputs.get("rent_growth") is not None:
            challenges.append(f"Rent growth input is {inputs['rent_growth']:.2%}; returns remain sensitive to this assumption.")
        if inputs.get("exit_cap_rate") is not None:
            challenges.append(f"Exit cap input is {inputs['exit_cap_rate']:.2%}; valuation sensitivity remains material.")
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
