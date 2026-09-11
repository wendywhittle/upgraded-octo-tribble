# CRE Scenario Analysis

## Purpose

CRE Scenario Analysis answers one analytical question:

> What happens to the underwriting if these explicit inputs change?

It does not forecast which scenario will occur and does not authorize investment.

## Architectural Position

```text
VALIDATED UNDERWRITING INPUTS
        ↓
SCENARIO DEFINITIONS
        ↓
EXPLICIT OVERRIDES
        ↓
CRE UNDERWRITING CALCULATION ENGINE
        ↓
SCENARIO OUTPUTS
        ↓
INDEPENDENT SIMULATION (FUTURE)
```

The scenario layer defines explicit input variation. The existing deterministic calculation engine performs financial calculations.

## Scenario Definitions

The boundary supports the existing analytical case labels:

- `base`
- `upside`
- `downside`
- `stress`
- `adversarial`

Labels describe analytical cases. They do not carry probabilities.

## Explicit Overrides

Overrides are limited to inputs already accepted by the deterministic calculation engine, including gross potential income, vacancy credit loss, operating expenses, property value, cap rate, loan amount, LTV, principal, interest rate, amortization years, and equity invested.

Underwriting fields that require a new financial transformation are not silently converted. For example, `vacancy_rate` is not turned into `vacancy_credit_loss` by this layer.

Missing values remain unresolved. Zero is never used as a missing-data substitute.

## Deterministic Recalculation

A scenario copies the compatible base underwriting inputs, applies only explicit overrides, and calls the existing calculation functions. The original underwriting artifact is never mutated.

The same base inputs, overrides, and calculation version produce the same calculation results.

No random sampling, stochastic paths, Monte Carlo, or scenario probability assignment exists in this boundary.

## Provenance

Each scenario records:

- scenario identity and type
- base underwriting reference
- explicit override references
- calculation references
- calculation formula version
- creation time
- scenario status
- uncertainty

Scenario provenance is distinct from evidence provenance.

## Epistemic Boundary

```text
Evidence ≠ Finding
Finding ≠ Assumption
Assumption ≠ Calculation
Calculation ≠ Projection
Projection ≠ Scenario
Scenario ≠ Simulation
Simulation ≠ Recommendation
Recommendation ≠ Authorization
```

A scenario is an analytical case, not a fact or evidence. A scenario output is a calculation result, not a recommendation.

## Due Diligence Relationship

Due diligence remains upstream. A finding may later inform an explicitly authored analytical assumption, but this module does not transform findings into assumptions or estimate capex automatically.

## Underwriting Relationship

The scenario engine consumes the immutable CRE underwriting/pro forma boundary and maps only directly compatible fields into calculation inputs. It does not redesign underwriting or introduce a second financial model.

## Calculation Engine Relationship

`app/scenario_analysis.py` orchestrates input variation and calls `app/underwriting_calculations.py`. Financial formulas are not duplicated in the scenario layer.

## Future Simulation Relationship

Scenarios provide explicit cases that a future independent simulation boundary may consume. Simulation is responsible for modeled uncertainty and distributions. Scenario Analysis is not a probabilistic layer.

## Governance

The scenario boundary is research-only, deterministic, non-authoritative, non-executing, non-transactional, and non-portfolio-mutating.

It cannot allocate capital, submit offers, negotiate, acquire property, contact lenders or brokers, execute transactions, authorize investments, or mutate portfolio state.

The Investment Case and Human Decision Gate remain downstream. Tools are capabilities, not permissions.

## Deliberate Non-Goals

This boundary does not add:

- Monte Carlo or stochastic simulation
- probability models or scenario probabilities
- market forecasting
- autonomous underwriting or investment decisions
- automated assumptions or capex estimation
- lender/broker integrations or acquisition infrastructure
- transaction execution or capital allocation
- portfolio management
- persistence, vector/graph databases, warehouse, CRM, ETL, OCR, or lease abstraction
- external environmental, title, zoning, or assessor APIs
- a new evidence or due diligence framework
- Charter changes
- a duplicate financial calculation framework
