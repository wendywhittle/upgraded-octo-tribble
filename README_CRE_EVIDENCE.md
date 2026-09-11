# CRE Evidence / Evidence Normalization Boundary

## Purpose

This boundary establishes the canonical internal representation of real-world CRE evidence attributable to a specific opportunity.

**REAL WORLD → CRE OPPORTUNITY / DEAL → CRE EVIDENCE → CLAIMS / INTERPRETATIONS**

CRE evidence is informational and research-only. It does not authorize action.

## CRE Evidence boundary

`CREEvidence` is an immutable, opportunity-scoped source observation. It preserves the observed value or source content, category, subject, epistemic status, provenance, uncertainty, integrity references, conflicts, and historical relationships.

## Relationship to generic Evidence

The repository's existing generic evidence layer remains the integrity gate. CRE evidence uses a thin validation adapter rather than creating a competing validation framework. Existing timestamp, freshness, provenance, source-identity, corroboration, and synthetic-demo restrictions remain in force.

## Relationship to CRE Opportunity / Deal

Every CRE evidence record carries a stable `opportunity_id`. The opportunity can retain evidence IDs through its existing `evidence_refs` field. Evidence does not embed the entire opportunity object.

## Provenance rules

Source, source type/reference, publisher where available, observed/effective/retrieved timestamps, point-in-time status, and provenance metadata remain attached to the evidence. Missing information remains missing rather than being inferred.

## Epistemic distinctions

Evidence records source material or observations. They do not become claims, interpretations, assumptions, projections, recommendations, or authorizations. `observed`, `sourced`, `unresolved`, and `superseded` remain explicit evidence states.

## Conflict handling

Contradictory observations coexist. Conflict and contradictory-evidence references provide traceability without overwriting either source. Resolution is downstream reasoning/governance work.

## Historical and supersession behavior

Evidence is immutable. A later observation can reference the evidence it supersedes while the earlier record remains reconstructable.

## Governance

The boundary explicitly carries `investment_authority = "none"`. Execution, transaction, and portfolio-mutation capabilities are false. Evidence cannot authorize investment, acquisition, offers, financing, or capital allocation.

## Non-goals

This boundary does not implement scraping, LoopNet/MLS or broker/property APIs, browser research, CRM, warehouse/ETL, vector/graph storage, document-processing systems, screening, due diligence, underwriting expansion, lender acquisition, capital allocation, transaction execution, autonomous acquisition, portfolio management, new persistence, or changes to `CHARTER.md`.
