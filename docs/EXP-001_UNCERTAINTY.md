# EXP-001 — Dependence-Aware Uncertainty

The preregistered EXP-001 point estimates remain unchanged. This document defines a secondary uncertainty analysis for the incremental Brier, log-loss, and AUC differences.

## Why blocks are required

EXP-001 labels a future five-trading-day window. Adjacent observations therefore share future sessions and are not independent. A naive IID bootstrap can understate uncertainty.

The sensitivity implementation uses a circular moving-block bootstrap with a default block length of five observations. The block length is a methodological sensitivity choice tied to the locked five-day horizon; alternative block lengths should be reported rather than selected after seeing the result.

## What is reported

For each incremental metric:

- preregistered point estimate
- bootstrap confidence interval
- confidence level
- number of valid resamples
- block length
- deterministic seed
- method identifier

A bootstrap resample that contains only one outcome class is discarded because AUC and the comparative evaluation are not identifiable in that sample. The analysis fails closed if too few valid resamples remain.

## Interpretation boundary

These intervals are uncertainty estimates around the observed out-of-sample metric differences. They do not establish causality, economic value, trading profitability, or a hypothesis decision by themselves.

Results must also be examined for chronological stability, methodology-version changes, missingness, and sensitivity to dependence assumptions before any scientific conclusion is considered.

The analysis remains research-only: no brokerage connection, order generation, portfolio mutation, or autonomous action is permitted.
