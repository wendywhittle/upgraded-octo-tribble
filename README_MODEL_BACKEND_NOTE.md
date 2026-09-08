# Model backend implementation note

The guarded callable backend is intentionally vendor-neutral. It receives structured
context and returns candidate reasoning only. AgentRunner remains responsible for
schema validation and capability enforcement. The default provider remains
ContractModelProvider, so adding a backend does not change deterministic behavior.
