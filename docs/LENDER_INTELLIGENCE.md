# Lender Intelligence Data Contract

## Phase 8A

Phase 8A establishes the smallest provenance-aware contract for representing externally supplied lender and financing information.

The architectural boundary is:

```text
LENDER INFORMATION
        ↓
PROVENANCE / EVIDENCE
        ↓
STRUCTURED FINANCING TERMS
        ↓
CAPITAL STACK
        ↓
FINANCING ANALYSIS
```

The module is a data contract. It is deliberately not a scraper, matching engine, ranking engine, recommendation engine, communication agent, or financing execution system.

## Data Model

### `LenderProfile`

Represents descriptive lender identity and stated scope:

- lender identity and name
- lender type
- asset types
- geographies
- provenance records

### `FinancingTerms`

Represents externally supplied terms that may later be consumed by Capital Stack analysis:

- loan program/type
- loan-size range
- stated maximum LTV/LTC
- stated minimum DSCR/debt yield
- stated interest rate and rate type
- amortization and maturity
- recourse
- conditions
- applicability
- evidence status
- provenance
- unresolved questions
- explicit unresolved conflicts

Missing values remain unknown. They are not converted into favorable assumptions.

## Provenance

Every lender profile and financing-term record requires at least one `ProvenanceRecord`.

The record preserves:

- provenance category
- source
- source date when available
- observed date/time
- optional review date
- freshness status
- verification status

The project provenance vocabulary remains:

`FACT`, `SOURCE`, `ASSUMPTION`, `HYPOTHESIS`, `CALCULATION`, `INTERPRETATION`, `PREDICTION`, `RECOMMENDATION`.

External lender information is represented as sourced evidence by default. A lender statement does not silently become an authoritative calculated result.

## Freshness

Freshness is explicit rather than inferred by an autonomous timer. The contract supports `CURRENT`, `AGING`, `STALE`, and `UNKNOWN`.

No universal stale threshold is imposed in Phase 8A. Source dates and observation dates remain available for later policy-specific review.

## Uncertainty

The contract preserves conditional, estimated, incomplete, and contradictory information. Conditions and applicability are represented directly, while unresolved questions remain visible.

Unknown is different from invalid.

## Conflict Handling

Conflicting observations are retained rather than resolved automatically.

For example, a lender's published 75% maximum LTV and a deal-specific 65% quoted maximum LTV may coexist as separate financing-term records with separate provenance and an explicit unresolved conflict.

The data contract never chooses the winning value.

## Capital Stack Boundary

Lender Intelligence represents supplied terms. Capital Stack calculates financing consequences.

For example:

```text
Lender Intelligence:
minimum DSCR requirement = 1.25x

Capital Stack:
actual DSCR = 1.38x
```

Actual DSCR, actual LTV/LTC, debt yield, debt service, principal reduction, balloon balance, equity requirement, and leveraged cash flow remain Capital Stack calculations. This module does not duplicate those calculations.

## Scenario and Contrarian Compatibility

Phase 8A creates no second scenario engine and no financing Monte Carlo engine.

The contract preserves financing attributes that future scenario and Contrarian analysis may consume, including leverage constraints, floating/fixed rate information, maturity, recourse, conditions, refinancing considerations, and unresolved evidence.

Those downstream components remain responsible for their own analytical roles.

## Future Scraper Boundary

The future source-monitoring architecture is:

```text
LENDER SOURCES
        ↓
SCRAPER / INGESTION
        ↓
RAW SOURCE CAPTURE
        ↓
PROVENANCE + FRESHNESS
        ↓
STRUCTURED LENDER TERMS
        ↓
CAPITAL STACK
```

A future scraper must feed this contract rather than bypass it. Raw source evidence, dates, applicability, conditions, and verification state should be preserved. Scraped information must not become authoritative financing calculations merely because it was collected automatically.

No scraper or web crawler is implemented in Phase 8A.

## Future Lender Comparison Boundary

A later analytical comparison layer may filter or compare lender information. That does not create authority to select a lender.

The intended separation is:

```text
DATA FILTERING
        ↓
ANALYTICAL COMPARISON
        ↓
HUMAN LENDER SELECTION
```

Highest score, lowest rate, or apparent eligibility must never silently become an approval or lender-selection decision.

## Governance

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

This module:

- represents lender information
- preserves provenance and uncertainty
- preserves conflicts
- supplies structured terms for future analysis

It does not:

- determine financing approval
- authorize capital
- select a lender
- rank lenders
- recommend a lender
- contact lenders
- submit applications
- negotiate terms
- create commitments
- deploy capital
- execute financing or transactions
- mutate workflow state

`CHARTER.md` remains authoritative and is unchanged by Phase 8A.
