# AletheiaTelos Evidence Pipeline

The research boundary is deliberately one-way:

`SOURCE -> NORMALIZE -> EVIDENCE -> INTEGRITY -> CORROBORATION -> AGENT REASONING`

External sources are read-only. The RSS/Atom adapter performs HTTPS GET requests only and records retrieval and source-observed timestamps without inventing point-in-time provenance.

## Configuration

Set `ALETHEIA_RESEARCH_FEEDS` to a comma-separated list of HTTPS RSS/Atom feed URLs. If unset, the `/research/evidence` route is not registered, so the application has no implicit external data dependency.

## Boundary guarantees

- No brokerage connectivity.
- No order or write capability.
- Raw source documents are normalized before agent use.
- Evidence must pass the existing integrity gate.
- Stale, malformed, or non-point-in-time evidence can be rejected.
- Research acquisition does not perform reasoning or synthesis.
- Tests use injected fetchers; CI does not depend on external network availability.
