# AletheiaTelos Institutional Investment Intelligence

AletheiaTelos is expanding from an institutional CRE intelligence platform into a broader research architecture for **Institutional Investment Intelligence**.

This is an architectural expansion, not a replacement of the CRE system.

## Two Engines

### Capital Engine

The Capital Engine provides a provider-neutral boundary for research across:

- Public markets
- Quantitative research
- Alternative data
- Macro
- Factors
- Market regimes
- Risk
- Portfolio research

### Asset Engine

The existing real-asset orientation remains the Asset Engine:

- CRE
- Industrial
- NNN
- Infrastructure
- Development
- Private assets
- Operations
- Capital structure

Both engines share the same downstream intelligence architecture.

## Shared Intelligence Loop

```text
REAL WORLD
    ↓
DATA / EVIDENCE
    ↓
EVIDENCE REGISTRY
    ↓
INTELLIGENCE
    ↓
COMPUTATIONAL KALEIDOSCOPE
    ↓
CONFLICT / COEXISTENCE
    ↓
INDEPENDENT SIMULATION
    ↓
CONTRARIAN / SKEPTIC REVIEW
    ↓
HUMAN INVESTMENT COMMITTEE
    ↓
DECISION
    ↓
OUTCOME
    ↓
ATTRIBUTION
    ↓
EPISTEMIC MEMORY
    ↓
NEXT THESIS
```

## Alternative Data Boundary

External providers are inputs, not authorities.

```text
DATA PROVIDERS
    ↓
NORMALIZATION
    ↓
EVIDENCE REGISTRY
    ↓
INTEGRITY / PROVENANCE / FRESHNESS
    ↓
CORROBORATION
    ↓
AGENT REASONING
```

The Capital Engine exposes a small `EvidenceSource` registry so providers can be added without coupling the investment architecture to any single vendor. Quiver can therefore be integrated later as an optional alternative-data provider without becoming a required dependency.

No credentials or paid-provider configuration belongs in the repository.

## Cross-Asset Intelligence

The shared domain vocabulary supports typed relationships between capital-market entities and real assets without requiring a graph database at this stage.

Examples of future research paths include:

```text
company activity
    ↓
government contracts
    ↓
capital expenditure
    ↓
infrastructure
    ↓
geography
    ↓
industrial demand
    ↓
CRE opportunity
```

and:

```text
CRE / infrastructure / industrial activity
    ↓
companies / suppliers
    ↓
public securities
    ↓
macro implications
    ↓
capital allocation hypotheses
```

These relationships remain evidence-backed. A relationship or hypothesis does not become an observation merely because an agent proposes it.

## Epistemic Boundary

The system preserves the distinction:

```text
OBSERVATION
    ↓
EVIDENCE
    ↓
INTERPRETATION
    ↓
HYPOTHESIS
    ↓
SCENARIO ASSUMPTION
    ↓
SIMULATION
```

The independent simulation layer remains responsible for scenario distributions and uncertainty. Agent conclusions supply assumptions and competing hypotheses rather than determining simulation results.

## Governance Boundary

AletheiaTelos remains a research and decision-intelligence system.

The Capital Engine does **not** provide:

- Brokerage connectivity
- Order submission
- Autonomous trading
- Portfolio mutation
- Independent investment authority

The Human Investment Committee remains an explicit decision boundary.

The purpose of the expansion is to increase the breadth of research while preserving the distinction between intelligence and authority.
