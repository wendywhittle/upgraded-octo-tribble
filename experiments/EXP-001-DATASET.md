# EXP-001 Dataset Acquisition Contract

This file defines the data contract for the first empirical run of Experiment #001.

## Required series

- SPX close
- VIX close
- Cboe SKEW close

## Required provenance per observation

- `observed_at`
- `available_at`
- `source_id`
- source/version identifier
- methodology version for each methodology-sensitive series
- dataset/content hash

## Point-in-time rule

`available_at` must be no later than `observed_at` for information used to construct an observation. Future labels may only use observations strictly after the prediction timestamp and must never enter the feature set.

## SKEW methodology rule

The empirical dataset must identify the exact SKEW methodology/version used. If a provider supplies a revised historical series, the revision must receive a distinct dataset identity rather than silently replacing a prior run.

## Acquisition boundary

AletheiaTelos does not scrape restricted/delayed quote pages and does not embed provider credentials. The ingestion boundary accepts an authorized historical export or licensed feed and records its identity and provenance.

## Reproducibility

Before an empirical result is accepted, record:

1. dataset ID;
2. source/version;
3. methodology version;
4. schema version;
5. SHA-256 content hash;
6. observation date range;
7. row count;
8. manifest fingerprint;
9. locked EXP-001 specification identity.

The current repository's synthetic fixture remains mechanics-only and is not evidence for H1 or H0.
