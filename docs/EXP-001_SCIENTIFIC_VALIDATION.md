# EXP-001 Scientific Validation Boundary

Experiment #001 asks whether SKEW adds incremental information about subsequent SPX drawdowns after controlling for recent SPX behavior and VIX.

This document defines what the execution result must establish before any empirical conclusion is considered credible.

## Required checks

1. **Point-in-time integrity** — every observation must have provenance and must have been available no later than its observation timestamp.
2. **Immutable dataset identity** — the exact input dataset, source/version, methodology version, and canonical content hash must be recorded.
3. **Chronological evaluation** — the preregistered 70/30 split remains unchanged for the primary result; no random shuffling is permitted.
4. **Outcome identifiability** — both positive and negative drawdown outcomes must occur in both training and test windows. If a window is single-class, the primary evaluation stops rather than reporting a misleading AUC or degenerate model result.
5. **Class-balance visibility** — the execution result reports event counts and the test event rate so a reader can judge whether the holdout contains enough information to interpret the metrics.
6. **No synthetic evidence** — repository fixtures test mechanics only and must never be presented as evidence for the SKEW hypothesis.
7. **Methodology provenance** — SKEW observations must carry a methodology/version identifier because historical methodology changes can affect comparability.
8. **No automatic hypothesis declaration** — metric improvements are evidence to investigate, not an automatic declaration that H1 is true.

## Primary metrics

The locked primary comparison reports Brier score and log loss. AUC is secondary. Lower Brier/log loss and higher AUC favor the augmented model, but the magnitude, uncertainty, data quality, and stability of any improvement must be assessed before interpretation.

## Next validation layer

After an authorized historical dataset is available, the next engineering/scientific pass should add explicitly versioned sensitivity analyses for overlapping five-day horizons and uncertainty estimation without changing the preregistered primary result. Those analyses must remain separate from the locked primary specification.

## Governance

EXP-001 remains a research and decision-intelligence experiment. It does not place trades, connect to a brokerage, mutate portfolio state, or authorize execution.
