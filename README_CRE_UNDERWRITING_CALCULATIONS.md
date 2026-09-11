# CRE Underwriting Calculation Engine

## Purpose

This boundary provides deterministic financial calculations for explicit CRE underwriting inputs. It calculates; it does not authorize investment.

## Architectural position

**CRE Evidence → Due Diligence → Explicit Underwriting Inputs → Calculation Engine → Pro Forma / Return Outputs**

The engine sits downstream of the typed underwriting representation and upstream of future scenario analysis, independent simulation, contrarian review, synthesis, and the Human Decision Gate.

## Current calculations

The first boundary contains deterministic functions for:

- effective gross income
- net operating income
- cap rate
- implied value
- loan amount from explicit LTV
- annual debt service from explicit amortization terms
- DSCR
- LTV
- cash flow after debt service
- cash-on-cash return

IRR, equity multiple, sale proceeds, terminal value modeling, growth projections, and scenario generation remain outside this boundary unless their required inputs and a separate coherent calculation seam are established later.

## Inputs and missing data

Inputs are explicit. The engine does not invent vacancy, expenses, cap rates, financing terms, exit assumptions, holding periods, or other missing values. Undefined denominator cases return an explicit `unresolved` result rather than zero.

## Provenance and epistemic boundary

Each calculation result preserves its calculation type, explicit input values, optional input references, and formula version. Calculated outputs remain calculations. They do not become evidence, findings, assumptions, recommendations, or authorization.

## Due diligence relationship

Due diligence findings may inform an explicit downstream underwriting assumption, but the calculation engine does not perform that transformation automatically.

**Finding → Explicit Assumption → Calculation**

## Scenario and simulation relationship

The functions are repeatable with different explicit inputs, making them compatible with future scenario analysis. Scenario generation and Monte Carlo/distributional simulation are separate boundaries.

## Governance

The engine is deterministic, analytical, research-only, non-executing, non-transactional, and non-portfolio-mutating. It cannot authorize investment or alter portfolio state. The Human Decision Gate remains downstream.

## Deliberate non-goals

No scenario engine, Monte Carlo engine, automated assumption generation, market forecasting, capex estimation, lender acquisition, scraping, transaction execution, offer generation, capital allocation, portfolio management, new persistence, or Charter changes are part of this boundary.
