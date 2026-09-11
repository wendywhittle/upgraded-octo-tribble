# Meta-Intelligence / Investment Case Synthesis

Phase 6 establishes a deterministic synthesis boundary above the existing analytical engines.

## Responsibility

Meta-Intelligence reconciles existing:

- evidence
- agent perspectives
- conflict and disagreement
- deterministic Pro Forma outputs
- Scenario results
- Monte Carlo / CRE Simulation Adapter outputs
- Contrarian findings
- unresolved questions

It identifies convergence, divergence, dominant risks, thesis dependencies, scenario fragility, evidence gaps, and questions requiring human review.

It does not independently calculate financial metrics or run simulations.

## Calculation boundaries

**SCENARIOS VARY ASSUMPTIONS.**

**PRO FORMA CALCULATES.**

**SIMULATORS STRESS.**

**CONTRARIAN ATTACKS.**

**META-INTELLIGENCE SYNTHESIZES.**

**META-INTELLIGENCE DOES NOT DECIDE.**

IRR, NOI, valuation, equity multiple, probability of loss, drawdown, and simulation percentiles remain authoritative outputs of their originating engines. The synthesis layer consumes those values and may interpret them, but does not recompute them.

## Disagreement

Disagreement is preserved as structured data. The synthesis layer supports:

- AGREEMENT
- MINOR_DISAGREEMENT
- MATERIAL_DISAGREEMENT
- UNRESOLVED
- INSUFFICIENT_DATA

No consensus is manufactured merely to produce a cleaner thesis.

## Thesis status

The analytical thesis may be classified as:

- SUPPORTED
- CONDITIONAL
- FRAGILE
- UNSUPPORTED
- UNDETERMINED

These classifications are analytical interpretations. They are not workflow states, authorization decisions, or investment approvals.

No numerical investment score is introduced.

## Evidence and provenance

Evidence conflicts remain visible. Missing or unresolved material evidence is surfaced rather than silently resolved.

Synthesis preserves the project's provenance distinction:

`FACT → SOURCE → ASSUMPTION → HYPOTHESIS → CALCULATION → INTERPRETATION → PREDICTION → RECOMMENDATION`

Synthesis output is primarily `INTERPRETATION`. Additional diligence is `RECOMMENDATION`. Calculated values retain `CALCULATION` provenance from their originating engine.

## Contrarian integration

The Contrarian asks:

> HOW COULD THIS INVESTMENT LOSE?

Meta-Intelligence asks:

> WHAT IS THE MOST DEFENSIBLE UNDERSTANDING OF THE CASE AFTER CONSIDERING THE AVAILABLE EVIDENCE, PERSPECTIVES, CALCULATIONS, SCENARIOS, SIMULATIONS, AND CONTRARIAN FINDINGS?

Material Contrarian findings and unresolved questions are carried into synthesis rather than discarded.

`NO_GO_RECOMMENDATION` remains a recommendation. It does not reject a deal, change workflow state, create authorization, or create a portfolio position.

## InvestmentCase integration

`apply_synthesis_to_case()` returns a copied `InvestmentCase` with synthesis fields populated. It does not mutate the original case and does not modify workflow state or human authorization records.

## Human authority

Meta-Intelligence cannot:

- authorize underwriting
- authorize capital structure
- authorize an investment
- reject a deal at the workflow level
- create authorization events
- create portfolio positions
- deploy capital
- execute transactions

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

## Architecture

```text
EVIDENCE
↓
AGENT REASONING
↓
VALIDATED ASSUMPTIONS
↓
PRO FORMA
↓
SCENARIOS
↓
CRE SIMULATION ADAPTER
↓
EXISTING MONTE CARLO
↓
DISTRIBUTIONAL RISK
↓
CONTRARIAN / ADVERSARIAL REVIEW
↓
META-INTELLIGENCE / SYNTHESIS
↓
[future] CAPITAL STACK
↓
[future] INVESTMENT COMMITTEE
```
