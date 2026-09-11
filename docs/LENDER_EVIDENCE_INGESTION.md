# Structured Lender Evidence Ingestion

## Phase 8B

Phase 8B establishes the controlled boundary through which externally supplied lender information enters the Phase 8A lender intelligence contract.

```text
LENDER SOURCES
      ↓
RAW SOURCE EVIDENCE
      ↓
STRUCTURED INGESTION
      ↓
PROVENANCE / FRESHNESS / VERIFICATION
      ↓
STRUCTURED LENDER TERMS
      ↓
CAPITAL STACK
```

The ingestion layer validates and copies supplied records into the existing Phase 8A models. It does not interpret evidence, calculate financing consequences, resolve conflicts, select lenders, or authorize actions.

## Provenance and freshness

Source, source date, observed time, optional review date, freshness status, and verification status are preserved by the Phase 8A contract. Missing dates remain unknown. The ingestion boundary does not invent freshness thresholds or upgrade evidence to fact.

Applicability, conditions, unresolved questions, and evidence status remain attached to the supplied financing terms.

## Conflicts

Conflicting observations are retained as separate financing-term records. The ingestion layer validates explicit conflict references but never chooses a winning value.

## Unknown vs invalid

Missing information remains `None` or an explicit `UNKNOWN` status according to the data contract. Structurally invalid supplied information is rejected. The system does not manufacture missing financial terms.

## Calculation boundary

Lender-supplied terms remain source-derived evidence. Capital Stack remains authoritative for actual transaction calculations including DSCR, LTV, LTC, debt yield, debt service, principal reduction, balloon balance, equity requirement, and leveraged cash flow.

The ingestion layer performs none of these calculations.

## Future scraper compatibility

A future automated source-monitoring system should capture raw source evidence first and then submit it through this same ingestion boundary:

```text
AUTOMATED SCRAPER
      ↓
RAW SOURCE CAPTURE
      ↓
PHASE 8B INGESTION
      ↓
PROVENANCE / FRESHNESS
      ↓
STRUCTURED LENDER TERMS
```

No scraper is implemented here. The boundary exists so automation can later fill the same controlled receptacle rather than bypassing provenance and validation.

## Non-goals

Phase 8B does not implement:

- scraping or automated discovery
- lender APIs
- lender matching, ranking, scoring, or recommendation
- lender selection
- outreach or negotiation
- applications or commitments
- financing approval or capital authorization
- portfolio or transaction execution
- financing Monte Carlo
- underwriting or scenario engines

## Governance

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

`CHARTER.md` remains authoritative. The ingestion layer creates no authorization surface and cannot execute financing or transactions.
