# CRE Opportunity / Deal Boundary

## Purpose

The CRE Opportunity / Deal boundary is the canonical upstream representation of a real-world commercial real-estate investment opportunity.

It answers **what opportunity are we reasoning about?** without deciding whether the opportunity should be pursued.

The boundary is deliberately research-only:

**REAL WORLD → CRE OPPORTUNITY / DEAL → EVIDENCE → CLAIMS → ASSUMPTIONS → UNDERWRITING → SCENARIOS → SIMULATION → CONTRARIAN → CAPITAL STACK → INVESTMENT CASE → HUMAN DECISION GATE**

## Epistemic boundaries

- Property identity is not an investment opportunity.
- An opportunity is not evidence.
- Evidence is not a claim.
- An observed fact is not an underwriting assumption.
- A deal term is not a projection.
- A model output is not an investment fact.
- A recommendation is not authorization.

Observed and sourced observations retain their status and provenance. Unknown and unresolved fields remain explicit. Conflicting observations can coexist and remain traceable through evidence and conflict references.

A later opportunity version references the earlier opportunity rather than mutating historical state.

## Integration

`CREOpportunityDeal` can be referenced by CRE underwriting through `opportunity_id` and can be carried directly by `StructuredInvestmentCase` through `opportunity_deal`.

Neither integration grants authority or execution capability.

## Governance

The boundary explicitly carries:

- `investment_authority = "none"`
- `execution_capability = false`
- `portfolio_mutation = false`
- `authorization_capability = false`

The object describes an opportunity. It does not submit offers, allocate capital, contact lenders, execute transactions, or authorize investment.

## Deliberate non-goals

This boundary does not implement opportunity scraping, broker/MLS integrations, CRM functionality, a data warehouse, lender APIs, transaction execution, autonomous acquisition, a full underwriting engine, new persistence infrastructure, vector/graph storage, or changes to `CHARTER.md`.
