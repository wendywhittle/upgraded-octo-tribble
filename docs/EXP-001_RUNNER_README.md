# EXP-001 Runner

`app/experiment_001_runner.py` is the narrow execution boundary for authorized historical CSV data. It validates the dataset, constructs an immutable manifest, builds point-in-time observations, and invokes the locked EXP-001 evaluator.

It has no network fetch, credential, brokerage, order, or portfolio capability.
