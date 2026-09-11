# CRE Contrarian / Adversarial Underwriting

The Contrarian is a deterministic analytical review layer. It consumes existing Pro Forma, Scenario, Simulation, evidence, and agent-perspective outputs and asks:

> How could this investment lose?

It does not recalculate financial or Monte Carlo outputs and it does not make authorization decisions.

## Responsibility

The Contrarian identifies explicit failure modes such as revenue weakness, occupancy stress, expense escalation, exit-cap sensitivity, evidence gaps, and unresolved assumptions. It can recommend additional diligence and can represent a NO_GO_RECOMMENDATION, but that recommendation never changes workflow state.

## Calculation boundaries

- **SCENARIOS VARY ASSUMPTIONS.**
- **PRO FORMA CALCULATES.**
- **SIMULATORS STRESS.**
- **CONTRARIAN ATTACKS.**
- **CONTRARIAN DOES NOT DECIDE.**

The Contrarian consumes `ProFormaResult` rather than duplicating NOI, valuation, IRR, equity-multiple, or cash-flow formulas. Simulation metrics such as probability of loss, percentiles, and drawdown are consumed from the existing Monte Carlo result.

## Scenario and simulation review

Scenario overrides remain hypotheses. Simulation outputs remain calculations. A review can inspect BASE, UPSIDE, DOWNSIDE, and ADVERSARIAL cases when those results are supplied together.

The review preserves scenario identity and simulation seed identity and does not mutate the supplied objects.

## Provenance

Findings distinguish hypothesis/assumption inputs from calculated simulation outputs and from Contrarian interpretation or recommendation. Missing evidence is reported explicitly rather than treated as favorable evidence.

Contradictory evidence remains a structured input for future Meta-Intelligence and Epistemic Memory work.

## Margin of safety

The review exposes machine-readable components such as valuation cushion, downside deterioration, probability of loss, downside percentile, drawdown, assumption sensitivity, evidence strength, and unresolved risks. Where the current architecture does not provide a calculation, the component is explicitly marked as not assessed rather than recomputed locally.

The current implementation uses `THIN` or `UNDETERMINED` conservatively. It does not create an opaque composite score.

## Agent boundary

Agent perspectives are reasoning inputs only. The review rejects agent fields that attempt to provide authoritative calculated outputs such as IRR, NOI, valuation, probability of loss, or drawdown.

## Human authority

The Contrarian cannot approve, reject, authorize, change workflow state, create authorization events, create portfolio positions, deploy capital, or execute transactions.

`NO_GO_RECOMMENDATION` is an analytical recommendation. Human authorization remains the governing decision boundary.

## InvestmentCase

`InvestmentCase` already provides `contrarian_findings`, `margin_of_safety`, `agent_perspectives`, and `disagreement` fields. Phase 5 therefore does not redesign the case envelope. Future orchestration can attach the structured review without overwriting deterministic calculations or simulation results.

## Future direction

The review is intentionally a foundation for future Meta-Intelligence, Investment Committee analysis, and Epistemic Memory. It is not an autonomous investment engine.

AGENTS REASON.
EVIDENCE SUPPORTS.
MODELS CALCULATE.
SCENARIOS VARY ASSUMPTIONS.
SIMULATORS STRESS.
CONTRARIAN ATTACKS.
WORKFLOW ORCHESTRATES.
HUMANS AUTHORIZE.

AUTOMATION BETWEEN GATES.
HUMAN AUTHORITY AT GATES.
