# CRE Opportunity Screening

## Purpose

The CRE Opportunity Screening boundary sits between the canonical opportunity/evidence layer and deeper underwriting.

**REAL WORLD → CRE OPPORTUNITY / DEAL → CRE EVIDENCE → OPPORTUNITY SCREENING → CRE UNDERWRITING**

Screening asks whether the evidence currently available warrants additional investment-analysis effort. It is a research filter, not an investment decision.

## Boundary

`CREOpportunityScreening` is an immutable, opportunity-scoped analytical artifact. It records explicit screening criteria, evidence references, uncertainty, positive and negative factors, unresolved issues, missing critical evidence, risk flags, and a constrained disposition:

- `PASS`: sufficient apparent fit to justify deeper analysis
- `FAIL`: a supported screening-level disqualifier exists
- `HOLD`: a material issue or conflict requires resolution
- `INSUFFICIENT_DATA`: reliable evidence is not sufficient for a meaningful determination

Unknown information is not converted into failure or assumption.

## Epistemic Integrity

Screening criteria preserve their own status and remain distinct from source evidence, claims, assumptions, recommendations, and authorization. Conflicting or missing evidence remains visible through explicit states and references.

Existing CRE evidence and provenance contracts are reused. Screening does not create a competing evidence-validation framework.

## History

Screening artifacts are immutable. A later screening can reference a prior screening through `supersedes_screening_id` without mutating historical state.

## Governance

Screening is research-only. It has no investment authority, execution capability, transaction capability, portfolio mutation capability, or authorization capability. `PASS` is not approval, and `FAIL` is not an investment recommendation.

## Downstream

A screening result can be carried by the Structured Investment Case and is conceptually upstream of CRE underwriting. It does not bypass the Human Decision Gate.

## Deliberate Non-Goals

This boundary does not implement scraping, broker or property APIs, CRM, warehouse/ETL, market-data acquisition, underwriting calculations, due diligence, lease abstraction, tenant-credit analysis, transaction execution, capital allocation, portfolio management, autonomous acquisition, new persistence, or Charter changes.
