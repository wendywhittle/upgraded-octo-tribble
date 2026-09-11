# CRE Underwriting & Pro Forma Boundary

## Purpose

AletheiaTelos now has a typed boundary for CRE underwriting and property-level pro forma artifacts.

**THE PRO FORMA IS A MODEL OF ASSUMPTIONS, NOT A STATEMENT OF FACT.**

**UNDERWRITING SUPPORTS INVESTMENT REASONING. IT DOES NOT AUTHORIZE INVESTMENT.**

## Boundary

The boundary represents, where supported:

- property and deal identity
- acquisition terms
- operating assumptions
- valuation assumptions
- financing references
- modeled cash flows
- modeled return outputs
- provenance, dates, uncertainty, and status

Observed property performance remains distinguishable from underwritten assumptions. A sourced input is not silently converted into an assumption, and a modeled output is not represented as an investment fact.

## Epistemic statuses

Underwriting artifacts use explicit status values:

`observed` · `sourced` · `assumed` · `calculated` · `projected` · `scenario` · `simulated` · `unresolved` · `superseded`

The boundary preserves the distinction:

**Evidence ≠ Assumption ≠ Calculation ≠ Projection ≠ Scenario ≠ Simulation Result ≠ Investment Fact**

## Integration

The `CREUnderwritingProForma` is an optional typed component of the `StructuredInvestmentCase`. It can reference the existing `CapitalStack` and lender-evidence IDs without creating lender commitments or financing authorization.

The existing independent simulation and Contrarian layers remain analytically separate. The underwriting boundary does not determine simulation results or authorize a recommendation.

## Governance

The artifact is immutable and permanently research-only:

- `investment_authority = "none"`
- `execution_capability = False`
- `portfolio_mutation = False`

The Human Decision Gate remains downstream. A recommendation is not authorization.

## Deliberate non-goals

This boundary does **not** add:

- a full CRE financial calculation engine
- automated lender acquisition
- financing commitments
- investment execution
- portfolio mutation
- persistence or vector/graph infrastructure
- Charter changes

Missing data remains missing. The system must document the gap rather than fabricate a pro forma.
