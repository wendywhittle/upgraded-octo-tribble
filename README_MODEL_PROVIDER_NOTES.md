# Model Provider Implementation Notes

The provider boundary is intentionally vendor-neutral. A production adapter should convert a model response into the existing agent assessment contract, preserve evidence provenance, expose model/provider/version metadata, and fail closed on malformed output.

It must not receive credentials or execution tools. Risk simulation remains independent of model conclusions.
