# AletheiaTelos Reasoning Boundary

AletheiaTelos keeps **evidence acquisition** separate from **agent reasoning**.

`SOURCE -> NORMALIZE -> EVIDENCE -> INTEGRITY -> REASONING -> CONFLICT -> RISK -> SKEPTIC -> SYNTHESIS -> GOVERNANCE`

## Design rules

- Evidence must pass the integrity gate before it becomes decision-usable.
- Reasoning receives inspectable evidence and preserves provenance.
- Missing or blocked evidence produces `NO_DATA`, not manufactured confidence.
- Agent confidence is an assessment, not a probability of investment success.
- Monte Carlo simulation remains independent of agent conclusions.
- Skeptic/Contrarian review remains downstream of independent risk simulation.
- Human decision authority remains mandatory.
- No brokerage connectivity, order placement, trading credentials, or portfolio execution exists in this layer.

The current implementation is deterministic and provider-agnostic. A future model-backed agent may replace the deterministic assessment, but the evidence, risk, skeptic, and governance boundaries must remain intact.
