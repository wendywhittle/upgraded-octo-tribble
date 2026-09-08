# AletheiaTelos Stooq Market Provider

AletheiaTelos now has a concrete, read-only external market-data provider backed by Stooq's daily CSV endpoint.

Flow:

`STOOQ -> MARKET OBSERVATION -> EVIDENCE -> INTEGRITY -> REASONING`

## Safety boundary

- The provider performs read-only HTTP GET requests.
- It has no brokerage integration or order capability.
- It accepts no trading credentials.
- It does not rank securities, predict prices, construct portfolios, or execute decisions.
- Network access is isolated to the provider; the Monte Carlo engine remains network-independent.
- Tests inject a fetch function and therefore do not require external network access.

## Point-in-time handling

Stooq's daily CSV supplies a trading date rather than an intraday timestamp. The adapter normalizes that date to midnight UTC and retains `timeframe="1d"` so downstream systems can see the timestamp precision boundary rather than treating it as an intraday observation.

## Symbol mapping

Provider-specific symbols can be supplied explicitly, for example `{"SPX": "^spx"}`. The adapter otherwise lowercases the requested symbol for the provider query.

The provider is intentionally small. Additional providers should implement the same `MarketDataSource` contract and pass through the same evidence integrity gate rather than creating provider-specific reasoning paths.
