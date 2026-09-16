# External Capital Ecosystem

ALETHEIA TELOS represents external capital providers as provider-independent, read-only ecosystem participants.

The first represented participant is **PrideCo Loans**.

## Boundary

An external capital provider may be a potential financing counterparty and a source of capital-market information. Its public or supplied financing information is not automatically authoritative evidence.

The intended evidence boundary is:

`external provider -> financing observation -> provenance -> validation -> validated evidence -> institutional analysis`

A financing observation remains distinct from evidence. Only an explicitly `VALIDATED` observation carrying an `evidence_id` may cross into the existing evidence boundary, where the normal evidence validator applies timestamp, provenance, freshness, and decision-usability controls.

The resulting evidence preserves provider identity, observation timestamp, source URI/label, financing terms, asset-class and geographic scope, assumptions, limitations, and validation metadata. Missing financing information remains missing; the adapter does not invent terms.

Validated financing evidence may inform analytical perspectives, risk simulation, conflict analysis, and an institutional investment case. It does not constitute financing approval, a financing commitment, lender selection, investment approval, execution authority, or portfolio authority.

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

## Institutional analysis boundary

Once validated, financing evidence enters the same evidence-fed analytical pathway used by other validated evidence. Existing perspectives may independently analyze capital-structure implications, and existing conflict/coexistence and independent risk-simulation semantics remain in force.

The system must preserve uncertainty rather than fabricate missing financing terms. Conflicting perspectives remain conflicts rather than being collapsed into consensus.

The financing evidence adapter does not create or grant:

- lending approval
- financing commitments
- lender selection authority
- automated lender outreach
- investment approval
- execution authority
- portfolio authority
- capital-transfer capability
- brokerage connectivity

Human investment authority remains the sole authorization boundary.

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
