# EXP-001 Execution API

The application exposes `POST /experiments/EXP-001/run` for an authorized canonical CSV payload.

The endpoint is intentionally narrow:

- accepts only the canonical EXP-001 CSV schema;
- enforces point-in-time provenance and immutable dataset identity through the existing runner;
- requires a single source/version/methodology identity per run;
- performs research-only evaluation;
- never fetches market data, scrapes providers, connects to a brokerage, places orders, or mutates a portfolio.

The endpoint does not accept arbitrary model parameters, alter the preregistered experiment specification, or declare H1/H0 automatically.
