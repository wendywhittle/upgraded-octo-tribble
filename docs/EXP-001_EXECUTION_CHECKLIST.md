# EXP-001 Execution Checklist

Use this checklist when an authorized historical dataset is available.

- [ ] Confirm the dataset is an authorized export or licensed feed.
- [ ] Preserve the raw source outside the repository when redistribution is restricted.
- [ ] Confirm every row has source ID, source version, methodology version, and content provenance.
- [ ] Confirm `observed_at` and `available_at` are timezone-aware and normalize consistently.
- [ ] Confirm no duplicate normalized observation timestamps exist.
- [ ] Confirm no point-in-time violation exists.
- [ ] Verify immutable dataset ID, canonical content hash, and manifest are recorded.
- [ ] Verify at least 30 constructed observations are available.
- [ ] Verify both positive and negative drawdown outcomes exist in training and test windows.
- [ ] Confirm the preregistered EXP-001 primary specification is unchanged.
- [ ] Run the locked primary result before any sensitivity analysis.
- [ ] Record baseline and augmented Brier score, log loss, and AUC.
- [ ] Review event counts and test event rate before interpreting metrics.
- [ ] No synthetic fixture is presented as empirical evidence.
- [ ] Run separately versioned sensitivity analyses for overlapping horizons, dependence, uncertainty, and chronological stability.
- [ ] Have the Skeptic/Contrarian layer review data integrity, metric differences, uncertainty, and failure modes.
- [ ] Keep hypothesis interpretation separate from execution: no automatic H1/H0 declaration.
- [ ] Human authority remains required for any consequential decision.
