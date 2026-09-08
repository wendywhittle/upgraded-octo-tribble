# Next architecture milestone

The next implementation step is to adapt one real model SDK behind `CallableModelProvider`.
The SDK integration must remain outside the Agent, AgentRunner, evidence, risk, skeptic,
synthesis, and governance layers. Credentials and network access must be isolated to that
adapter, with explicit timeouts and failures represented as non-authoritative research
errors. No brokerage or execution capability is part of the integration.
