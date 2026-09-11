# CRE Evidence / Evidence Normalization Boundary

Canonical immutable representation of real-world CRE evidence attributable to a specific opportunity.

**REAL WORLD → CRE OPPORTUNITY / DEAL → CRE EVIDENCE / NORMALIZATION → CLAIMS / INTERPRETATIONS**

## Boundary

`CREEvidence` preserves source observations, opportunity identity, category, subject reference, epistemic status, provenance, uncertainty, integrity results, corroboration/dependency relationships, conflicts, and historical supersession.

Evidence is source material or an observation. It is not a claim, interpretation, assumption, projection, recommendation, authorization, or investment fact.

## Existing evidence integrity

The existing generic evidence validator remains the single integrity gate. CRE evidence uses a thin adapter to reuse timestamp validation, freshness, provenance, source identity, and synthetic-demo restrictions. No competing evidence framework is introduced.

## Opportunity relationship

Every record carries a stable `opportunity_id`. The canonical opportunity already retains evidence IDs through `evidence_refs`. Evidence does not embed the full opportunity.

## Conflicts and history

Contradictory records coexist without overwriting source observations. Conflict references and explicit supersession references preserve traceability and historical reconstruction.

## Governance

CRE evidence is research-only: `investment_authority = "none"`, with execution, transaction, and portfolio-mutation capabilities disabled. Evidence cannot authorize acquisition, offers, financing, capital allocation, or any other consequential action.

## Non-goals

No scraper, LoopNet/MLS integration, broker/property API, browser research, CRM, warehouse/ETL, vector or graph storage, new persistence, screening, due diligence engine, underwriting expansion, lender acquisition, capital allocation, transaction execution, autonomous acquisition, portfolio management, or Charter modification.
