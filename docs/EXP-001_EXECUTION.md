# EXP-001 Execution Protocol

Experiment #001 is now ready to accept an authorized historical dataset.

## Execution order

1. Obtain SPX, VIX, and CBOE SKEW observations from an authorized export or licensed feed.
2. Preserve the original source file and its acquisition metadata outside the research engine when redistribution is restricted.
3. Convert the source into `experiments/EXP-001_DATA_TEMPLATE.csv` without changing the preregistered experiment specification.
4. Require timezone-aware `observed_at` and `available_at` timestamps. Normalize them to UTC at validation.
5. Validate source identity, source version, methodology version, row-level provenance, positive market values, uniqueness, and point-in-time availability.
6. Compute the immutable dataset content hash and construct the dataset manifest.
7. Build the locked 5-day features and future drawdown labels from the validated observations.
8. Run the baseline and SKEW-augmented models using the existing EXP-001 specification.
9. Report Brier score, log loss, AUC, and incremental improvements without changing the hypothesis after seeing results.
10. Send the resulting distribution of evidence and model metrics through the Skeptic/Contrarian review before any synthesis.

## Evidence rule

A successful mechanics test is not empirical evidence. No conclusion about SKEW's predictive value may be declared until an authorized historical dataset has passed the full provenance and point-in-time boundary.

## Safety boundary

This protocol is research-only. It does not place trades, connect to a brokerage, hold trading credentials, transfer capital, or mutate portfolio state. Any consequential decision remains subject to human authorization.
