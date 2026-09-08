# Guarded Model Backend

AletheiaTelos now has a vendor-neutral backend seam for model inference.

`app/model_backend.py` provides `CallableModelBackend` and `CallableModelProvider`.
A caller supplies a callable that receives structured context containing the question,
agent identity/role/horizon/capabilities, and validated evidence.

## Safety boundary

The backend is deliberately not a tool executor and does not import a model-vendor SDK.
The context explicitly declares the system as research-only. Model output still passes
through `AgentRunner`, where it is validated against the `AgentOutput` contract and
where execution, brokerage, and portfolio-mutation capabilities remain disabled.

`ContractModelProvider` remains the deterministic default. A real model SDK can later
be adapted behind this seam without changing the orchestration architecture.
