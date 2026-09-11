# CRE Evidence / Evidence Normalization Boundary

Canonical immutable representation of real-world CRE evidence attributable to a specific opportunity.

**REAL WORLD → CRE OPPORTUNITY / DEAL → CRE EVIDENCE → CLAIMS / INTERPRETATIONS**

CRE evidence is informational and research-only. It does not authorize action.

## Boundary

`CREEvidence` preserves observed value or source content, category, subject, epistemic status, provenance, uncertainty, integrity references, conflicts, and historical relationships.

## Generic Evidence

The existing generic evidence layer remains the integrity gate. CRE evidence uses a thin validation adapter rather than a competing validation framework. Existing timestamp, freshness, provenance, source identity, corroboration, and synthetic-demo restrictions remain in force.

## Opportunity relationship

Every CRE evidence record carries a stable `opportunity_id`. The opportunity retains evidence IDs through its existing `evidence_refs` field. Evidence does not embed the full opportunity.

## Epistemic and provenance rules

Evidence records source material or observations. They do not become claims, interpretations, assumptions, projections, recommendations, or authorizations. `observed`, `sourced`, `unresolved`, and `superseded` remain explicit evidence states. Source identity and temporal provenance stay attached to the evidence.

## Conflicts and history

Contradictory observations coexist. Conflict references provide traceability without overwriting either source. A later evidence record may reference the evidence it supersedes while the earlier record remains immutable and reconstructable.

## Governance

`investment_authority = "none"`. Execution, transaction, and portfolio-mutation capabilities are false. Evidence cannot authorize investment, acquisition, offers, financing, or capital allocation.

## Non-goals

No scraping, LoopNet/MLS or broker/property APIs, browser research, CRM, warehouse/ETL, vector/graph storage, document-processing platform, screening, due diligence, underwriting expansion, lender acquisition, capital allocation, transaction execution, autonomous acquisition, portfolio management, new persistence, or `CHARTER.md` changes.
