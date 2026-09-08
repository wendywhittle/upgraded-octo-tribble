# EXP-001 data pipeline

1. Obtain SPX, VIX, and SKEW history from an authorized source.
2. Preserve the provider export unchanged outside the repository when redistribution is restricted.
3. Convert it to the strict ingestion schema required by `app/experiment_001_csv.py`.
4. Require `available_at <= observed_at`, source identity, source version, SKEW methodology version, and source content hash.
5. Compute the repository dataset fingerprint.
6. Create the immutable experiment manifest before fitting any model.
7. Run the preregistered EXP-001 evaluation unchanged.
8. Send the empirical distribution and metrics to Skeptic/Contrarian review before synthesis.

No step in this pipeline has brokerage, execution, portfolio mutation, or capital-transfer capability.
