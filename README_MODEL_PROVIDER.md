# AletheiaTelos Model Provider Boundary

AletheiaTelos now has a provider-agnostic model boundary behind `AgentRunner`.

## Flow

`validated evidence -> agent role/context -> provider -> structured assessment -> downstream conflict/risk/skeptic`

`CallableModelProvider` is a narrow adapter for a caller-owned model function. It receives only:

- agent identity and role
- research horizon
- the question
- evidence that already passed the evidence-integrity gate

The adapter does not expose brokerage, credentials, order placement, execution, or portfolio mutation interfaces.

The runner reasserts the research-only capability flags on returned assessments rather than trusting provider output.

The default provider remains `ContractAgentProvider`, so existing deterministic behavior is preserved until a real model provider is explicitly supplied.

The model provider is therefore a reasoning component, not an authority or execution surface. Monte Carlo risk remains independent of agent conclusions, Skeptic remains downstream, and human decision authority remains mandatory.
