# Guarded Model Backend

AletheiaTelos has a vendor-neutral provider seam and one real model implementation.

`validated evidence -> AgentRunner -> ModelProvider -> AgentOutput`

The deterministic `ContractModelProvider` remains the regression/default path when
no model API key is configured. When `ALETHEIA_MODEL_API_KEY` is present, only the
`researcher` perspective is routed to the configured OpenAI Responses model. All
other perspectives continue through the deterministic contract provider.

## Real Researcher configuration

Set these environment variables in the deployment environment:

- `ALETHEIA_MODEL_API_KEY` — required to enable the real model.
- `ALETHEIA_MODEL_NAME` — optional; defaults to `gpt-5.6-terra`.
- `ALETHEIA_MODEL_ENDPOINT` — optional; defaults to the OpenAI Responses endpoint.

No model SDK is required; the backend uses the standard-library HTTP client.

## Safety boundary

The real backend receives the question, Researcher role, validated evidence, and
advisory institutional learning. It does not receive tools, brokerage credentials,
execution functions, or portfolio mutation capabilities.

Model output must satisfy a strict structured-output contract. Evidence references
must point to supplied evidence IDs; the backend rejects forged or unknown evidence
references. The AgentRunner also rejects authority-escalating output and enforces
research-only capabilities and human decision authority.

When no decision-usable evidence reaches Researcher, the backend returns `NO_DATA`
and does not call the model.

Monte Carlo simulation remains downstream and independent of agent conclusions.
Agents may contribute explicit assumptions, but they do not determine simulation
paths or outcomes.
