# EXP-001 Validation Boundary

The primary EXP-001 evaluator now refuses to report model metrics when the chronological training or test window contains only one outcome class. Execution output includes event counts and test event rate so empirical results cannot hide a degenerate holdout.

This is a software-quality safeguard, not evidence for the SKEW hypothesis.
