# Phase 6.5: Integration Validation / Architectural Hardening

Phase 6.5 validates the analytical spine before Capital Stack work begins. It does not add a new analytical engine.

## Validated chain

```text
EVIDENCE
↓
AGENT REASONING
↓
VALIDATED ASSUMPTIONS
↓
PRO FORMA
↓
SCENARIOS
↓
CRE SIMULATION ADAPTER
↓
EXISTING MONTE CARLO
↓
DISTRIBUTIONAL RISK
↓
CONTRARIAN / ADVERSARIAL REVIEW
↓
META-INTELLIGENCE / SYNTHESIS
↓
STRUCTURED INVESTMENT CASE
```

## Authority boundaries

**SCENARIOS VARY ASSUMPTIONS.**

**PRO FORMA CALCULATES.**

**SIMULATORS STRESS.**

**CONTRARIAN ATTACKS.**

**META-INTELLIGENCE SYNTHESIZES.**

**META-INTELLIGENCE DOES NOT DECIDE.**

Financial calculations remain authoritative in their originating engines. Synthesis consumes those outputs and interprets them without recomputation.

## Integration validation

The hardening suite verifies:

- deterministic end-to-end synthesis from existing analytical outputs
- calculation provenance remains `CALCULATION`
- synthesis remains `INTERPRETATION`
- recommendations remain `RECOMMENDATION`
- agent-supplied IRR and probability values cannot become authoritative
- scenario and simulation outputs are consumed rather than recalculated
- Pro Forma, Scenario, Simulation, and Contrarian results are not mutated
- contradictory evidence and material disagreement remain visible
- unresolved conditions produce conditional or explicitly insufficient conclusions
- no numerical investment score is introduced
- InvestmentCase integration is copy-only
- workflow state and human authorization records remain unchanged
- synthesis is deterministic for identical structured inputs

## Governance boundary

Meta-Intelligence cannot authorize underwriting, capital structure, or investment. It cannot reject a deal at the workflow level, create authorization events, create portfolio positions, deploy capital, or execute transactions.

A thesis classification such as `SUPPORTED`, `FRAGILE`, or `UNSUPPORTED` is an analytical classification, not a workflow transition.

A `NO_GO_RECOMMENDATION` remains a recommendation. It does not become an authorization or workflow rejection.

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

## Failure philosophy

The system must not manufacture certainty when analytical inputs are incomplete. Missing or unresolved conditions should fail explicitly or remain represented as `UNDETERMINED`, `UNRESOLVED`, or `INSUFFICIENT_DATA` where the existing contract permits.

The purpose of Phase 6.5 is to establish confidence in the architectural boundaries, not to optimize the analytical outputs or introduce another engine.
