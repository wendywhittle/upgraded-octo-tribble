"""Pre-registered evaluation engine for AletheiaTelos Experiment #001.

Question: does SKEW add incremental information about future SPX drawdowns
beyond recent SPX behavior and VIX?

This module is deliberately data-source agnostic. It evaluates a point-in-time
historical dataset after the experiment specification has been fixed. It does
not place trades, generate orders, or mutate portfolio state.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class Experiment001Spec:
    experiment_id: str = "EXP-001"
    question: str = (
        "Does SKEW contain incremental information about subsequent SPX "
        "drawdowns after controlling for recent SPX behavior and VIX?"
    )
    hypothesis: str = "SKEW adds incremental information after controlling for SPX behavior and VIX."
    null_hypothesis: str = "SKEW adds no meaningful incremental information."
    horizon_days: int = 5
    drawdown_threshold: float = -0.03
    train_fraction: float = 0.70
    seed: int = 42
    baseline_features: Tuple[str, ...] = ("spx_return_5d", "vix_level", "vix_change_5d")
    incremental_features: Tuple[str, ...] = ("skew_level", "skew_change_5d")


@dataclass(frozen=True)
class Observation:
    observed_at: str
    spx_return_5d: float
    vix_level: float
    vix_change_5d: float
    skew_level: float
    skew_change_5d: float
    future_max_drawdown: float


@dataclass(frozen=True)
class ModelMetrics:
    sample_count: int
    brier_score: float
    log_loss: float
    auc: float


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = exp(-x)
        return 1.0 / (1.0 + z)
    z = exp(x)
    return z / (1.0 + z)


def _standardize(train: Sequence[Sequence[float]], rows: Sequence[Sequence[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    if not train:
        raise ValueError("Training data cannot be empty.")
    width = len(train[0])
    means = [sum(row[i] for row in train) / len(train) for i in range(width)]
    scales = []
    for i in range(width):
        variance = sum((row[i] - means[i]) ** 2 for row in train) / len(train)
        scales.append(variance ** 0.5 or 1.0)
    transform = lambda row: [(row[i] - means[i]) / scales[i] for i in range(width)]
    return [transform(row) for row in train], [transform(row) for row in rows]


def _fit_logistic(x: Sequence[Sequence[float]], y: Sequence[int], iterations: int = 2500, learning_rate: float = 0.05) -> List[float]:
    if not x or len(x) != len(y):
        raise ValueError("Feature and outcome lengths must match and be non-empty.")
    if len(set(y)) < 2:
        raise ValueError("Training outcomes must contain both positive and negative classes.")
    width = len(x[0])
    weights = [0.0] * (width + 1)
    n = len(x)
    for _ in range(iterations):
        gradient = [0.0] * (width + 1)
        for row, target in zip(x, y):
            probability = _sigmoid(weights[0] + sum(weights[i + 1] * row[i] for i in range(width)))
            error = probability - target
            gradient[0] += error
            for i, value in enumerate(row):
                gradient[i + 1] += error * value
        for i in range(len(weights)):
            weights[i] -= learning_rate * gradient[i] / n
    return weights


def _predict(weights: Sequence[float], rows: Sequence[Sequence[float]]) -> List[float]:
    return [_sigmoid(weights[0] + sum(weights[i + 1] * row[i] for i in range(len(row)))) for row in rows]


def _auc(y: Sequence[int], probabilities: Sequence[float]) -> float:
    positives = [p for p, target in zip(probabilities, y) if target == 1]
    negatives = [p for p, target in zip(probabilities, y) if target == 0]
    if not positives or not negatives:
        raise ValueError("AUC requires both positive and negative classes in the evaluation set.")
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _metrics(y: Sequence[int], probabilities: Sequence[float]) -> ModelMetrics:
    if len(set(y)) < 2:
        raise ValueError("Evaluation outcomes must contain both positive and negative classes.")
    eps = 1e-12
    clipped = [min(1.0 - eps, max(eps, p)) for p in probabilities]
    brier = sum((p - target) ** 2 for p, target in zip(clipped, y)) / len(y)
    log_loss = -sum(target * log(p) + (1 - target) * log(1 - p) for p, target in zip(clipped, y)) / len(y)
    return ModelMetrics(len(y), brier, log_loss, _auc(y, clipped))


def _features(observation: Observation, names: Iterable[str]) -> List[float]:
    values = {
        "spx_return_5d": observation.spx_return_5d,
        "vix_level": observation.vix_level,
        "vix_change_5d": observation.vix_change_5d,
        "skew_level": observation.skew_level,
        "skew_change_5d": observation.skew_change_5d,
    }
    return [values[name] for name in names]


def evaluate_experiment_001(
    observations: Sequence[Observation],
    spec: Experiment001Spec = Experiment001Spec(),
) -> Dict[str, object]:
    """Run the pre-specified chronological baseline-vs-augmented comparison."""
    if len(observations) < 30:
        raise ValueError("Experiment #001 requires at least 30 observations for a meaningful split.")
    ordered = sorted(observations, key=lambda item: item.observed_at)
    split = int(len(ordered) * spec.train_fraction)
    if split < 20 or split >= len(ordered):
        raise ValueError("Training fraction leaves an invalid chronological split.")

    y = [int(item.future_max_drawdown <= spec.drawdown_threshold) for item in ordered]
    train_y, test_y = y[:split], y[split:]
    if len(set(train_y)) < 2:
        raise ValueError("Chronological training window contains only one outcome class; EXP-001 cannot be evaluated.")
    if len(set(test_y)) < 2:
        raise ValueError("Chronological test window contains only one outcome class; EXP-001 metrics are not identifiable.")

    baseline_train = [_features(item, spec.baseline_features) for item in ordered[:split]]
    baseline_test = [_features(item, spec.baseline_features) for item in ordered[split:]]
    augmented_train = [_features(item, spec.baseline_features + spec.incremental_features) for item in ordered[:split]]
    augmented_test = [_features(item, spec.baseline_features + spec.incremental_features) for item in ordered[split:]]

    baseline_train, baseline_test = _standardize(baseline_train, baseline_test)
    augmented_train, augmented_test = _standardize(augmented_train, augmented_test)
    baseline_probabilities = _predict(_fit_logistic(baseline_train, train_y), baseline_test)
    augmented_probabilities = _predict(_fit_logistic(augmented_train, train_y), augmented_test)
    baseline = _metrics(test_y, baseline_probabilities)
    augmented = _metrics(test_y, augmented_probabilities)

    return {
        "experiment_id": spec.experiment_id,
        "question": spec.question,
        "hypothesis": spec.hypothesis,
        "null_hypothesis": spec.null_hypothesis,
        "specification": {
            "horizon_days": spec.horizon_days,
            "drawdown_threshold": spec.drawdown_threshold,
            "baseline_features": list(spec.baseline_features),
            "incremental_features": list(spec.incremental_features),
            "train_fraction": spec.train_fraction,
            "chronological_split": True,
            "point_in_time_required": True,
        },
        "dataset_diagnostics": {
            "total_observations": len(ordered),
            "training_observations": len(train_y),
            "test_observations": len(test_y),
            "training_positive_events": sum(train_y),
            "training_negative_events": len(train_y) - sum(train_y),
            "test_positive_events": sum(test_y),
            "test_negative_events": len(test_y) - sum(test_y),
            "test_positive_rate": sum(test_y) / len(test_y),
        },
        "baseline": baseline.__dict__,
        "augmented": augmented.__dict__,
        "incremental": {
            "brier_improvement": baseline.brier_score - augmented.brier_score,
            "log_loss_improvement": baseline.log_loss - augmented.log_loss,
            "auc_improvement": augmented.auc - baseline.auc,
        },
        "governance": {
            "research_only": True,
            "human_decision_required": True,
            "execution_capability": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
        },
    }
