# AletheiaTelos — Independent CRE Simulation

## Purpose

The Independent CRE Simulation boundary models explicitly specified uncertainty around CRE underwriting inputs and produces descriptive outcome distributions. It is research and decision-intelligence infrastructure only.

## Boundary

The architectural boundary is:

**SCENARIO DEFINITIONS → INDEPENDENT SIMULATION → DISTRIBUTIONAL RISK OUTPUTS**

A **scenario** is an explicit analytical case with defined inputs or overrides.

A **simulation** samples explicitly modeled uncertainty and sends each sampled input set through the existing deterministic CRE underwriting calculation engine. It does not determine whether an outcome is good, bad, investable, or authorized.

## Explicit inputs

Each stochastic input records:

- input name
- deterministic/base value
- lower and upper bounds
- distribution type
- provenance reference

The initial boundary supports explicit `uniform` and `triangular` distributions. A triangular distribution uses the explicit deterministic value as its mode. No distribution is inferred from agent confidence, consensus, or qualitative language.

## Reproducibility

A simulation records:

- scenario reference
- iteration count
- random seed
- distribution configuration
- formula version
- provenance references
- creation time

The same scenario, inputs, configuration, iteration count, and seed produce the same modeled result.

## Deterministic calculation reuse

The simulation layer does not duplicate financial formulas. It dispatches sampled inputs to the existing calculation functions in `app/underwriting_calculations.py`.

## Distributional outputs

The current output boundary provides descriptive:

- mean
- median
- minimum
- maximum
- 5th, 25th, 50th, 75th, and 95th percentiles
- probability of crossing explicitly supplied thresholds

Threshold probabilities are descriptive only. For example, the simulator can report the modeled frequency of `DSCR < 1.20` when DSCR is the simulated metric. It does not interpret that frequency as a pass/fail decision.

## Epistemic status

Simulation output is **modeled** rather than observed. It is not evidence, a market fact, a due diligence finding, a historical outcome, a recommendation, or an authorization.

Due diligence findings do not automatically become probability distributions. Agent opinions and confidence values do not automatically become probability distributions.

## Provenance and immutability

Simulation artifacts and their input contracts are immutable. Provenance preserves the scenario, explicit stochastic inputs, seed, iteration count, distribution configuration, calculation formula version, and relevant references.

## Governance

The simulation boundary preserves:

- investment authority: `none`
- execution capability: `false`
- transaction capability: `false`
- portfolio mutation: `false`
- authorization capability: `false`

The simulator cannot execute transactions, allocate capital, modify portfolios, contact lenders or brokers, generate offers, or authorize investments.

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

## Limitations

This phase deliberately does not infer uncertainty from incomplete evidence. Missing inputs remain unresolved. The initial implementation models only explicit input distributions supported by the current deterministic calculation engine. It does not provide a forecast of real-world probabilities.

## Future integration

The simulation output is intended to feed a future **Contrarian / Adversarial Review** boundary. That review is not implemented here.

The intended architecture remains:

REAL WORLD → OPPORTUNITY / DEAL → EVIDENCE → SCREENING → DUE DILIGENCE → VALIDATED UNDERWRITING INPUTS → CRE UNDERWRITING CALCULATION ENGINE → PRO FORMA / RETURN OUTPUTS → SCENARIO ANALYSIS → INDEPENDENT SIMULATION → DISTRIBUTIONAL RISK → CONTRARIAN / ADVERSARIAL REVIEW → CAPITAL STACK → LENDER EVIDENCE → INVESTMENT SYNTHESIS → STRUCTURED INVESTMENT CASE → HUMAN DECISION GATE

Learning remains:

OUTCOME → OBSERVER → ATTRIBUTION → EPISTEMIC MEMORY → NEXT OPPORTUNITY

## Explicit non-goals

This boundary does not implement autonomous investment decisions, trading, recommendations, capital allocation, portfolio management, transaction execution, offer generation, lender or broker contact, acquisition automation, hidden probability assumptions, fabricated distributions, automated assumption generation, automated capex estimation, new evidence/due-diligence/underwriting frameworks, duplicated financial formulas, persistence infrastructure, vector or graph databases, warehouses, CRM, ETL, OCR, lease abstraction, external APIs, self-modification, Charter changes, or Contrarian / Adversarial Review.
