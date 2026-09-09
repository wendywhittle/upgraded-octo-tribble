# EXP-001 Sensitivity Analysis Plan

These analyses are secondary and do not alter the preregistered primary specification.

## Planned analyses after the authorized dataset is loaded

- **Horizon dependence:** quantify the effect of overlapping five-trading-day labels and add a time-aware sensitivity analysis.
- **Alternative dependence control:** evaluate a purged/embargoed chronological sensitivity design, preserving the locked 70/30 primary result unchanged.
- **Uncertainty:** estimate uncertainty around baseline-vs-augmented metric differences using a time-aware resampling method appropriate to serial dependence.
- **Stability:** inspect performance across chronological subperiods rather than relying only on the aggregate holdout.
- **Methodology breaks:** preserve SKEW methodology/version boundaries and report results separately when methodology changes make the history non-comparable.
- **Missingness:** report missing trading observations and verify that no imputation leaks future information.

## Interpretation rule

A sensitivity result that differs from the primary result does not invalidate the preregistered result; it identifies an uncertainty or dependence issue that must be disclosed. Conversely, a favorable primary result that disappears under reasonable dependence-aware sensitivity analysis must not be treated as robust evidence.

No sensitivity analysis may be used to search for a favorable specification and then retroactively relabel it as primary.
