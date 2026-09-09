"""Dependence-aware uncertainty utilities for EXP-001.

The primary experiment remains a fixed chronological evaluation. This module
provides a secondary moving-block bootstrap for uncertainty around metric
differences. Blocks are used because five-day forward labels overlap and are
therefore not safely treated as independent observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from random import Random
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class BootstrapInterval:
    metric: str
    estimate: float
    lower: float
    upper: float
    confidence: float
    resamples: int
    block_length: int
    seed: int
    method: str = "moving_block_bootstrap"

    def as_dict(self) -> Dict[str, object]:
        return self.__dict__.copy()


def _brier(y: Sequence[int], p: Sequence[float]) -> float:
    return sum((prob - target) ** 2 for target, prob in zip(y, p)) / len(y)


def _log_loss(y: Sequence[int], p: Sequence[float]) -> float:
    eps = 1e-12
    return -sum(
        target * log(min(1 - eps, max(eps, prob)))
        + (1 - target) * log(1 - min(1 - eps, max(eps, prob)))
        for target, prob in zip(y, p)
    ) / len(y)


def _auc(y: Sequence[int], p: Sequence[float]) -> float:
    positives = [prob for target, prob in zip(y, p) if target == 1]
    negatives = [prob for target, prob in zip(y, p) if target == 0]
    if not positives or not negatives:
        raise ValueError("AUC bootstrap requires both outcome classes.")
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            wins += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
    return wins / (len(positives) * len(negatives))


def metric_differences(
    y: Sequence[int],
    baseline_probability: Sequence[float],
    augmented_probability: Sequence[float],
) -> Dict[str, float]:
    """Return augmented-minus-baseline metric differences."""
    if not (len(y) == len(baseline_probability) == len(augmented_probability)):
        raise ValueError("Outcome and probability lengths must match.")
    if len(y) < 2 or len(set(y)) < 2:
        raise ValueError("Uncertainty analysis requires both outcome classes.")
    return {
        "brier_improvement": _brier(y, baseline_probability) - _brier(y, augmented_probability),
        "log_loss_improvement": _log_loss(y, baseline_probability) - _log_loss(y, augmented_probability),
        "auc_improvement": _auc(y, augmented_probability) - _auc(y, baseline_probability),
    }


def moving_block_bootstrap(
    y: Sequence[int],
    baseline_probability: Sequence[float],
    augmented_probability: Sequence[float],
    *,
    block_length: int = 5,
    resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> List[BootstrapInterval]:
    """Estimate uncertainty with a circular moving-block bootstrap.

    This is a sensitivity analysis, not a replacement for the preregistered
    point estimates. A circular block sampler preserves local dependence while
    avoiding arbitrary edge handling. The block length defaults to the locked
    five-trading-day horizon because the forward labels overlap on that scale.
    """
    n = len(y)
    if not (n == len(baseline_probability) == len(augmented_probability)):
        raise ValueError("Outcome and probability lengths must match.")
    if n < 10:
        raise ValueError("At least 10 evaluation observations are required.")
    if len(set(y)) < 2:
        raise ValueError("Evaluation outcomes must contain both classes.")
    if block_length <= 0 or block_length > n:
        raise ValueError("block_length must be between 1 and the evaluation size.")
    if resamples < 100:
        raise ValueError("At least 100 bootstrap resamples are required.")
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be between 0.5 and 1.0.")

    rng = Random(seed)
    values = {"brier_improvement": [], "log_loss_improvement": [], "auc_improvement": []}
    starts = list(range(n))
    blocks_needed = (n + block_length - 1) // block_length

    for _ in range(resamples):
        indices: List[int] = []
        for _ in range(blocks_needed):
            start = rng.choice(starts)
            indices.extend((start + offset) % n for offset in range(block_length))
        indices = indices[:n]
        sampled_y = [y[i] for i in indices]
        # AUC/log-loss/brier are undefined or unstable for a single-class draw.
        if len(set(sampled_y)) < 2:
            continue
        sampled_base = [baseline_probability[i] for i in indices]
        sampled_aug = [augmented_probability[i] for i in indices]
        diff = metric_differences(sampled_y, sampled_base, sampled_aug)
        for key, value in diff.items():
            values[key].append(value)

    minimum_valid = max(100, resamples // 2)
    if any(len(samples) < minimum_valid for samples in values.values()):
        raise ValueError("Too few valid bootstrap resamples contained both outcome classes.")

    alpha = (1.0 - confidence) / 2.0
    intervals: List[BootstrapInterval] = []
    point = metric_differences(y, baseline_probability, augmented_probability)
    for metric, samples in values.items():
        ordered = sorted(samples)
        lower = ordered[int(alpha * (len(ordered) - 1))]
        upper = ordered[int((1.0 - alpha) * (len(ordered) - 1))]
        intervals.append(
            BootstrapInterval(
                metric=metric,
                estimate=point[metric],
                lower=lower,
                upper=upper,
                confidence=confidence,
                resamples=len(samples),
                block_length=block_length,
                seed=seed,
            )
        )
    return intervals


__all__ = ["BootstrapInterval", "metric_differences", "moving_block_bootstrap"]
