# EXP-001 historical data acquisition contract

AletheiaTelos does not scrape delayed quote pages or embed vendor credentials. Historical observations must arrive through an authorized provider export or licensed feed and then pass the repository's provenance and point-in-time validation boundary.

## Required fields

`observed_at`, `available_at`, `source_id`, `source_version`, `methodology_version`, `content_hash`, `spx_close`, `vix_close`, `skew_close`.

`available_at` must not be later than `observed_at`. The SKEW methodology version is mandatory because a provider may revise methodology or historical calculations. A changed source export must therefore receive a new dataset identity rather than silently replacing an earlier research record.

## Experiment boundary

The acquisition layer supplies data; it does not choose the hypothesis, tune thresholds after observing results, or execute trades. EXP-001 remains locked to its preregistered 5-day horizon, -3% future-drawdown threshold, baseline SPX/VIX features, incremental SKEW features, and chronological split.

Synthetic fixtures in tests are mechanics tests only and are never empirical evidence.

## Operational rule

When an authorized historical SKEW export is available, place it outside the repository's source tree and ingest it through `app.experiment_001_csv.py`. Record the resulting dataset fingerprint and manifest before running the experiment. Never commit licensed/raw vendor data unless its redistribution rights explicitly permit it.
