# CRE Simulation Adapter

## Responsibility

The CRE Simulation Adapter is the translation boundary between deterministic CRE underwriting/scenarios and the existing independent Monte Carlo engine.

The flow is:

`Pro Forma -> Scenario -> CRE Simulation Adapter -> Existing Monte Carlo -> Distributional Risk`

The adapter does not perform Monte Carlo calculations. It validates the scenario by sending it through the existing Scenario Engine, preserves the resulting deterministic `ProFormaResult`, selects an explicit simulator regime, and invokes `run_monte_carlo()`.

## Scenario and Pro Forma separation

A ScenarioDefinition varies validated underwriting assumptions. The Pro Forma Engine then calculates revenue, expenses, NOI, valuation, cash flow, IRR, and equity multiple.

The adapter does not copy those formulas. The deterministic `ProFormaResult` is retained alongside the stochastic simulation result.

`SCENARIOS VARY ASSUMPTIONS.`

`PRO FORMA CALCULATES.`

`SIMULATORS STRESS.`

## Current simulator boundary

The existing simulator currently exposes a generic asset-value path model with four explicit stochastic regimes: `base`, `bull`, `bear`, and `adversarial`.

Phase 4 therefore maps the standard CRE scenario identities to those existing regimes:

- `BASE` -> `base`
- `UPSIDE` -> `bull`
- `DOWNSIDE` -> `bear`
- `ADVERSARIAL` -> `adversarial`

A custom CRE scenario must explicitly select one of the existing regimes.

This is intentionally a narrow adapter. It does **not** invent statistical distributions for rent growth, occupancy, expense growth, or exit cap rates. Those variables remain explicit CRE underwriting assumptions in the Scenario/Pro Forma layers. A future simulator-contract extension can add CRE-specific stochastic parameterization without moving stochastic logic into the adapter.

The current simulator uses the acquisition basis as its generic capital-at-risk starting value. Its stochastic regime parameters remain inside `app/simulator.py`.

## Reproducibility

`CRESimulationConfig` explicitly carries path count, optional horizon, seed, and simulator regime. With identical validated inputs and seed, the existing simulator produces reproducible results.

Different seeds may produce different stochastic results.

## Provenance and agent boundary

Scenario overrides remain hypotheses/assumptions. Simulation outputs are calculations.

An agent may propose an assumption such as `initial_occupancy = 0.88`, but it cannot provide `probability_loss`, `IRR`, NOI, valuation, or another calculated output as authoritative simulation data.

Calculated results always come from the Pro Forma Engine or existing Monte Carlo engine.

## InvestmentCase and workflow

`InvestmentCase.simulation_results` already exists and can hold structured simulation results without replacing the deterministic `proforma` or `scenarios` fields. Phase 4 does not add a new persistence layer or alter workflow transitions.

The adapter cannot authorize, reject, approve, create a portfolio position, deploy capital, execute a transaction, or bypass a human gate.

`SIMULATION` is analysis, not authority.

## Future architecture

The intended future chain is:

`PRO FORMA -> SCENARIOS -> CRE SIMULATION ADAPTER -> INDEPENDENT MONTE CARLO -> DISTRIBUTIONAL RISK -> CONTRARIAN`

A future CRE-specific simulation contract may model distributions for individual underwriting assumptions. That work belongs to a later, explicitly scoped extension of the simulation layer and must not be smuggled into the adapter.

`SIMULATION DOES NOT DECIDE.`

The institutional rule remains:

`AUTOMATION BETWEEN GATES.`

`HUMAN AUTHORITY AT GATES.`
