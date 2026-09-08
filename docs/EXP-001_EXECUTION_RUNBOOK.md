# EXP-001 Execution Runbook

1. Obtain an authorized historical SPX/VIX/SKEW dataset.
2. Preserve the raw source and acquisition metadata.
3. Convert to the strict EXP-001 CSV schema.
4. Validate timezone-aware timestamps, point-in-time availability, provenance, uniqueness, and positive values.
5. Compute the dataset fingerprint and manifest.
6. Construct locked five-day features and future drawdown labels.
7. Run the preregistered baseline and SKEW-augmented comparison.
8. Review metrics and evidence with the Skeptic/Contrarian layer.
9. Record the result without changing the specification after observing it.

Research-only. No live execution or portfolio mutation.