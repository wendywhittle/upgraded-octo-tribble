# Model Provider Boundary

AletheiaTelos now separates the agent contract from the model implementation.

`validated evidence -> AgentRunner -> ModelProvider -> AgentOutput`

The default `ContractModelProvider` preserves the existing deterministic behavior. A future model-backed provider can be substituted behind the same interface without changing orchestration, risk simulation, Skeptic review, synthesis, or governance.

Provider outputs are validated against `AgentOutput`. Invalid model output is rejected at the boundary.

Providers receive research inputs only. The runner explicitly rejects execution, brokerage, and portfolio-mutation capabilities and always marks human decision authority as required.
