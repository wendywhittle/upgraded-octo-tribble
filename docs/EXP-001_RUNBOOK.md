# EXP-001 Runbook

Run Experiment #001 only from an authorized historical CSV export.

1. Preserve the original authorized export outside the repository when redistribution is restricted.
2. Convert it to `experiments/EXP-001_DATA_TEMPLATE.csv` schema.
3. Supply explicit observation and availability timestamps plus source and methodology provenance.
4. Run `run_experiment_001_from_csv()`.
5. Verify the returned dataset content hash and manifest fingerprint are recorded with the result.
6. Review the empirical metrics with the Skeptic/Contrarian layer before interpretation.

The runner does not fetch data, scrape vendor pages, access credentials, connect to a brokerage, place orders, or mutate a portfolio. Synthetic fixtures are mechanics tests only and are not evidence for H1/H0.
