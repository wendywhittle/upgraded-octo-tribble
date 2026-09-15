# AletheiaTelos Institutional Core Audit v1

This pass establishes the shared institutional substrate beneath the existing analytical engines without adding execution capability.

## Canonical relationship

```text
Opportunity
    ↓
Evidence
    ↓
Investment Case
    ├── Perspectives + provenance
    ├── Conflict / Coexistence
    ├── Independent Risk Simulation
    └── Contrarian Review
    ↓
Decision Readiness
    ↓
Decision Gate
    ↓
Human Authority
    ↓
Decision Record
    ↓
Observation / Outcome / Attribution / Epistemic Memory
```

## What changed

- `app/institutional_core.py` establishes Opportunity identity and typed boundaries for evidence, conflict/coexistence, simulation, and Decision Record references.
- `app/institutional_investment_case.py` exposes canonical `investment_case_id` and `opportunity_id` and records perspective provenance.
- `app/decision_readiness.py` now evaluates explicit conditions and exposes mandatory, satisfied, blocking, provenance, and missing-evidence state.
- `app/analysis_pipeline.py` now creates an Opportunity before evidence-fed reasoning and links the resulting Investment Case to it.
- Generic risks and questions remain explicitly system-generated governance prompts rather than case-derived facts.

## Truth boundary

The pipeline does not manufacture a thesis merely to satisfy readiness. A case without an explicit thesis remains blocked from `OPEN_READY_FOR_HUMAN_AUTHORITY`.

Perspective separation is not treated as proof of model independence. Provenance records shared-input limitations.

The existing formal `app/decision_record.py` remains the human-input Decision Record boundary. Analytical-run history is not silently promoted to human authorization.

## Maturity

| Capability | Status |
|---|---|
| Opportunity | OPERATIONAL |
| Evidence validation | OPERATIONAL |
| Investment Case | OPERATIONAL |
| Perspective provenance | OPERATIONAL / independence still developing |
| Conflict / Coexistence | OPERATIONAL for current analytical outputs |
| Independent Risk Simulation | OPERATIONAL |
| Contrarian Review | OPERATIONAL |
| Decision Readiness | OPERATIONAL |
| Decision Gate | OPERATIONAL |
| Human Authority | REQUIRED / external |
| Formal Decision Record | OPERATIONAL as explicit-human-input boundary |
| Hold / Operate / Improve / Finance | DEVELOPING |
| Disposition | DEVELOPING |
| Outcome | DEVELOPING |
| Attribution | DEVELOPING |
| Epistemic Memory learning loop | DEVELOPING |
| Opportunity Acquisition adapters | ARCHITECTURALLY DEFINED |
| Capital Engine | DEVELOPING |
| Asset Engine | DEVELOPING |
| Autonomous execution | DISABLED |
| Brokerage | DISABLED |
| Portfolio mutation | DISABLED |
| Capital transfer | DISABLED |

No dashboard redesign, new workstation layer, external provider, database migration, or autonomous capability is part of this pass.
