# Deterministic CRE Pro Forma Engine

The Pro Forma Engine answers one question:

**What does the asset economically produce?**

## Responsibility

The engine converts validated CRE underwriting assumptions into deterministic asset-level operating and unlevered return calculations.

It is deliberately independent of:

- agents and LLM providers
- Monte Carlo simulation
- capital-stack analysis
- portfolio state
- investment approval

## Boundary

**Agents reason. Models calculate. Humans authorize.**

An agent may propose an assumption such as rent growth. The proposal is an input that must be validated. The engine calculates NOI, cash flow, valuation, and unlevered returns from the validated inputs. Agent output cannot directly become a calculated IRR or other authoritative financial result.

## Inputs and outputs

`ProFormaInput` contains the minimum asset-level acquisition, operating, capital-expenditure, growth, occupancy, and valuation assumptions required by the engine.

`ProFormaResult` contains calculated annual operating results, acquisition basis, entry and exit valuation, terminal value, unlevered cash flows, unlevered IRR, and unlevered equity multiple.

Calculated outputs are explicitly typed as `CALCULATION` in the result metadata.

## Determinism

The engine uses no LLM calls, agents, random values, external APIs, or time-dependent calculation state. Identical validated inputs produce identical results.

## InvestmentCase

A result can be attached to the Phase 1 `InvestmentCase` under `proforma`. The InvestmentCase remains the versioned institutional envelope. Future changes should preserve prior material underwriting versions rather than destructively rewriting them.

## Future components

The Pro Forma Engine is intentionally separate from:

- **Capital Stack Engine:** how the investment is financed.
- **Scenario Engine:** controlled assumption variations.
- **Simulation:** distributions of plausible outcomes.
- **Contrarian:** adversarial challenge of the thesis and assumptions.
- **Portfolio Engine:** state after an explicitly authorized investment.

The Pro Forma calculates. It does not decide.
