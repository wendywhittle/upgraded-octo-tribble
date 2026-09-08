# AletheiaTelos Market Data Boundary

Market data is treated as evidence, not as an instruction to trade.

`MARKET SOURCE -> NORMALIZE -> EVIDENCE -> INTEGRITY -> REASONING`

The adapter layer is provider-agnostic and read-only. A provider supplies normalized observations; the market-data pipeline converts them into provenance-rich evidence and applies the existing evidence integrity gate before downstream reasoning.

## Guarantees

- No brokerage connectivity.
- No order placement.
- No portfolio execution.
- No trading credentials.
- No prediction or synthesis in the acquisition layer.
- Point-in-time observations remain explicitly identifiable.
- Tests can use deterministic fixtures without external network access.

The next provider implementation should preserve these properties and should not make the Monte Carlo risk engine dependent on live network availability.
