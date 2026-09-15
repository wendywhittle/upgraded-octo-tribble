# AletheiaTelos Institutional Core Audit v1

## Audit conclusion

The repository already contains substantial analytical infrastructure: evidence validation, evidence-fed perspectives, typed conflict intelligence, independent simulation, skeptic/contrarian review, institutional investment-case assembly, Decision Readiness, Decision Gate, Observer, and append-only analytical-run history. The principal architectural weakness was not absence of intelligence components; it was the lack of a sufficiently explicit shared domain substrate tying them together.

This pass establishes that substrate without adding execution capability.

## Canonical institutional objects

### Opportunity

`app/institutional_core.py` establishes `Opportunity` as the object being evaluated. An Opportunity can exist before evidence is sufficient. It has stable identity, source, type, description, provenance, status, evidence references, and version metadata.

### Evidence

The existing evidence validation boundary remains authoritative. Invalid or unprovenanced evidence cannot become decision-usable. Evidence is kept conceptually separate from assumptions, calculations, scenarios, and simulations.

### Investment Case

`app/institutional_investment_case.py` remains the canonical analytical container. It now exposes `investment_case_id`, `opportunity_id`, perspective provenance, case-derived unresolved questions, and system-generated governance questions separately.

### Decision Readiness

`app/decision_readiness.py` now exposes mandatory conditions, satisfied conditions, blocking conditions, blocking reasons, missing evidence, unresolved issues, and perspective provenance. It produces a readiness state of `CLOSED_BLOCKED` or `OPEN_READY_FOR_HUMAN_AUTHORITY` while retaining the existing `status` compatibility value.

### Decision Gate

The existing Decision Gate continues to consume Decision Readiness. It does not infer authorization and does not create execution capability.

### Decision Record

`app/decision_record.py` already provides the formal immutable human-decision boundary. The analytical-run memory record is intentionally not treated as a human Decision Record. A formal Decision Record requires explicit human decision input.

### Outcome / Observation / Attribution / Epistemic Memory

These remain developing surfaces. This pass does not fabricate outcome or attribution data and does not create a vector or graph database.

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

## Important truth boundary

Generic governance prompts such as questions about invalidation, sensitivity, and margin of safety are explicitly marked as system-generated prompts. They are not represented as evidence-derived facts.

The current pipeline does not manufacture a thesis merely to satisfy readiness. Therefore a case with no explicit thesis remains blocked from `OPEN_READY_FOR_HUMAN_AUTHORITY`.

## Perspective independence

Perspective outputs are structurally separate, but shared pipeline inputs and deterministic providers do not by themselves establish independent model reasoning. Perspective provenance now records this limitation explicitly.

## Current maturity

| Capability | Status |
|---|---|
| Opportunity object | OPERATIONAL |
| Evidence validation | OPERATIONAL |
| Investment Case identity/container | OPERATIONAL |
| Perspective provenance | OPERATIONAL / developing analytical independence |
| Conflict / Coexistence | OPERATIONAL for current analytical outputs |
| Independent Risk Simulation | OPERATIONAL |
| Contrarian Review | OPERATIONAL |
| Decision Readiness contract | OPERATIONAL |
| Decision Gate | OPERATIONAL |
| Human Authority | REQUIRED / external to system |
| Formal Decision Record | OPERATIONAL as explicit human-input boundary |
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

## Deferred deliberately

No new external data provider, database migration, execution integration, dashboard redesign, workstation version, or autonomous capability was added in this pass.
