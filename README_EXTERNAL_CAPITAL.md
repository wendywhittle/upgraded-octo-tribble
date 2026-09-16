# External Capital Ecosystem

ALETHEIA TELOS represents external capital providers as provider-independent, read-only ecosystem participants.

The first represented participant is **PrideCo Loans**.

## Boundary

An external capital provider may be a potential financing counterparty and a source of capital-market information. Its public or supplied financing information is not automatically authoritative evidence.

The intended evidence boundary is:

`external observation -> provenance -> validation -> validated evidence`

Validated evidence may inform analytical perspectives, risk simulation, conflict analysis, and an institutional investment case. It does not grant the provider investment authority.

## Provider-independent financing observation

Financing information is represented separately from the provider registry as an immutable `FinancingObservation`.

The observation contract preserves:

- provider identity
- observation timestamp
- source URI/label when available
- financing type
- asset-class and geographic scope
- LTV/LTC when stated
- rate, term, and amortization when stated
- covenants, assumptions, and limitations
- explicit validation status
- evidence ID only when the observation has crossed the evidence boundary

A `VALIDATED` financing observation must carry an `evidence_id`. An `UNVALIDATED` observation remains an observation and cannot silently become evidence.

This allows future lenders, banks, family offices, institutional debt providers, equity providers, and strategic capital sources to use the same contract without creating provider-specific decision logic.

## PrideCo Loans

- Category: External Capital Provider / Private Real-Estate Lender
- Role: Potential financing counterparty and capital-market information source
- Relationship: External
- Authority: None
- Decision authority: None
- Execution authority: None
- Portfolio authority: None
- Investment approval authority: None
- Data access: None

No commercial, financing, data-sharing, endorsement, or partnership relationship is implied by this representation.

## Explicit exclusions

This subsystem does not provide:

- lending approval
- financing commitments
- capital transfers
- brokerage connectivity
- transaction execution
- portfolio mutation
- autonomous investment authority
- automated lender outreach

Human investment authority remains the sole authorization boundary.

## API

`GET /external-capital/manifest` exposes the read-only ecosystem manifest for the workstation and future provider-independent integrations.
