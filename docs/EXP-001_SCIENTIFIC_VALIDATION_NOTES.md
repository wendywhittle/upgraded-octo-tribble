# EXP-001 Scientific Validation Notes

The primary experiment remains locked: five-trading-day horizon, drawdown threshold of -3%, baseline SPX/VIX features, incremental SKEW features, and chronological 70/30 evaluation.

Before interpreting an empirical result, the execution must expose enough diagnostics to determine whether the holdout is statistically identifiable. In particular, both outcome classes must be present in training and test windows. A single-class window is now a hard validation failure rather than a metric that can be silently reported.

The result also exposes event counts and the test event rate. These are descriptive diagnostics, not additional model-selection criteria.

Secondary dependence and uncertainty analyses must remain versioned separately from the preregistered primary result. They may challenge robustness but may not replace the primary specification retroactively.

Synthetic fixtures in the repository exist only to test mechanics and are not empirical evidence.
