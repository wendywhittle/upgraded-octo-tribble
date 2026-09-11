# CRE Property Due Diligence Boundary

## Purpose

AletheiaTelos represents property-level due diligence findings as immutable analytical artifacts. Due diligence surfaces what is known, unknown, unresolved, conflicting, or potentially material without converting findings into investment decisions.

## Position in the architecture

**CRE Opportunity → CRE Evidence → Screening → Property Due Diligence → Underwriting**

Due diligence references the canonical `opportunity_id` and, when supported, `property_id`. It references existing `CREEvidence` rather than creating another evidence framework.

## Findings

Each `DueDiligenceFinding` preserves a category, topic, epistemic status, review status, finding/value, evidence references, uncertainty, materiality, risk flags, conflicts, and supersession where applicable.

Epistemic status remains separate from workflow/review status. Missing or unresolved information is represented explicitly rather than filled with assumptions.

## Unknowns and conflicts

The artifact can preserve unknown fields, missing documents, unresolved items, and conflicts. Conflicting findings coexist and historical findings are never overwritten. A later artifact can explicitly supersede an earlier one.

## Underwriting relationship

A finding may inform later analytical reasoning, but it does not silently become an underwriting assumption or calculation. The intended transformation remains:

**FINDING → ANALYTICAL INPUT → ASSUMPTION**

Those stages remain distinct.

## Governance

Due diligence is research-only. It has no investment authority, execution, transaction, portfolio mutation, or authorization capability. The Human Decision Gate remains downstream.

## Non-goals

This boundary does not perform inspections, order vendors, acquire documents, scrape CRE sources, integrate property/title/zoning APIs, abstract leases, calculate capex, run underwriting, execute transactions, allocate capital, manage portfolios, or add persistence/acquisition infrastructure.
