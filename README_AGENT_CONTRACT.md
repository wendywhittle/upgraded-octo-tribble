# AletheiaTelos Agent Contract

The agent layer is now an explicit research boundary rather than an implicit collection of demo functions.

## Contract

Each agent declares:

- `agent_id`
- `role`
- default reasoning horizon
- capability profile

Agents receive a question and already-acquired evidence. They return a structured assessment containing direction, confidence, thesis, evidence, assumptions, invalidation conditions, provenance, and capability metadata.

## Capability boundary

The registry rejects agents that declare:

- execution capability
- brokerage capability
- portfolio mutation capability

`human_decision_required` remains true for every assessment.

## Orchestration boundary

The registry is deliberately separate from:

`EVIDENCE -> AGENTS -> CONFLICT -> INDEPENDENT MONTE CARLO -> SKEPTIC -> SYNTHESIS -> OBSERVER -> MEMORY -> GOVERNANCE`

Agents do not control the Monte Carlo engine, Skeptic, governance, or execution. This keeps independent perspectives genuinely independent from the risk calculation and final authorization boundary.

The current `DeterministicAgent` is an adapter used to stabilize the contract. A future model-backed implementation can satisfy the same contract without changing downstream risk or governance controls.
